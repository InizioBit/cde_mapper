#!/usr/bin/env python
"""Reproducible Stage-0 retrieval experiment with per-source evidence."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def read_jsonl(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError(f"Gold dataset is empty: {path}")
    required = {"id", "query", "gold_ids"}
    for row in rows:
        missing = required - row.keys()
        if missing:
            raise ValueError(f"Gold row missing {sorted(missing)}: {row}")
    return rows


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_value(*args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args], cwd=REPO_ROOT, text=True, capture_output=True, check=False, timeout=10
        )
    except subprocess.TimeoutExpired:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def serialize_doc(doc, rank: int, source: str) -> dict:
    metadata = dict(doc.metadata or {})
    sid = str(metadata.get("sid", "")).strip()
    vocab = str(metadata.get("vocab", "")).strip().lower()
    scode = str(metadata.get("scode", metadata.get("code", ""))).strip()
    identifiers = [value for value in (sid, f"{vocab}:{scode}" if vocab and scode else "") if value]
    return {
        "rank": rank,
        "source": source,
        "identifiers": identifiers,
        "concept_id": sid or None,
        "code": scode or None,
        "label": metadata.get("label", doc.page_content),
        "vocabulary": vocab or None,
        "domain": metadata.get("domain"),
        "score": metadata.get("score"),
    }


def merge_candidates(source_docs: list[tuple[str, list]], topk: int) -> list[dict]:
    merged: list[dict] = []
    seen: set[str] = set()
    max_len = max((len(docs) for _, docs in source_docs), default=0)
    for index in range(max_len):
        for source, docs in source_docs:
            if index >= len(docs):
                continue
            item = serialize_doc(docs[index], len(merged) + 1, source)
            identity = "|".join(item["identifiers"]) or f"{item['label']}|{item['vocabulary']}"
            if identity.casefold() in seen:
                continue
            seen.add(identity.casefold())
            merged.append(item)
            if len(merged) == topk:
                return merged
    return merged


def invoke_timed(retriever, query: str) -> tuple[list, float, str | None]:
    started = time.perf_counter()
    try:
        return list(retriever.invoke(query)), round((time.perf_counter() - started) * 1000, 3), None
    except Exception as exc:  # diagnostic artifact must preserve failures
        return [], round((time.perf_counter() - started) * 1000, 3), repr(exc)


def invoke_athena_timed(retriever, query: str) -> tuple[list, float, str | None]:
    from rag.athena_api_retriever import convert_to_documents

    started = time.perf_counter()
    try:
        return convert_to_documents(retriever._fetch_from_athena(query)), round((time.perf_counter() - started) * 1000, 3), None
    except Exception as exc:
        return [], round((time.perf_counter() - started) * 1000, 3), repr(exc)


def points_to_documents(points) -> list:
    from langchain_core.documents import Document

    documents = []
    for point in points:
        payload = point.payload or {}
        metadata = dict(payload.get("metadata", payload))
        metadata.setdefault("score", point.score)
        content = payload.get("page_content") or payload.get("text") or metadata.get("label", "")
        documents.append(Document(page_content=str(content), metadata=metadata))
    return documents


def qdrant_query(client, collection: str, vector, vector_name: str, topk: int) -> tuple[list, float, str | None]:
    started = time.perf_counter()
    try:
        response = client.query_points(
            collection_name=collection,
            query=vector,
            using=vector_name,
            limit=topk,
            with_payload=True,
        )
        return points_to_documents(response.points), round((time.perf_counter() - started) * 1000, 3), None
    except Exception as exc:
        return [], round((time.perf_counter() - started) * 1000, 3), repr(exc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/baseline.yaml")
    parser.add_argument("--run-id")
    parser.add_argument("--max-queries", type=int)
    parser.add_argument("--skip-llm-check", action="store_true")
    args = parser.parse_args()

    os.chdir(REPO_ROOT)
    load_dotenv(REPO_ROOT / ".env")
    config_path = Path(args.config)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    params = config["default_params"]
    if params.get("device") == "cpu":
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
    paths = config["paths"]
    gold_path = Path(paths["gold_file"])
    rows = read_jsonl(gold_path)
    if args.max_queries is not None:
        rows = rows[: args.max_queries]
    run_id = args.run_id or datetime.now(timezone.utc).strftime("baseline-%Y%m%dT%H%M%SZ")
    output_dir = Path(paths["experiment_output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{run_id}.jsonl"
    manifest_path = output_dir / f"{run_id}.manifest.json"

    started_at = datetime.now(timezone.utc)
    from langchain_qdrant import FastEmbedSparse
    from qdrant_client import QdrantClient
    from qdrant_client.models import SparseVector
    from rag.athena_api_retriever import AthenaFilters, RetrieverAthenaAPI
    from rag.bi_encoder import SAPEmbeddings
    from rag.manager import LLMManager

    client = QdrantClient(
        url=params["qdrant_url"], port=int(params["qdrant_port"]), https=True, timeout=300
    )
    if not client.collection_exists(params["collection_name"]):
        raise RuntimeError(f"Qdrant collection does not exist: {params['collection_name']}")

    # Embed and query sequentially so the dense and sparse models never need to
    # coexist in the constrained WSL environment.
    dense_embedding = SAPEmbeddings(model_id=params["embedding_model"])
    dense_results = {}
    for row in rows:
        vector = dense_embedding.embed_query(row["query"])
        dense_results[row["id"]] = qdrant_query(
            client, params["collection_name"], vector, "omop_dense_vector", int(params["topk"])
        )
    del dense_embedding
    gc.collect()

    sparse_embedding = FastEmbedSparse(model_name=params["sparse_embedding_model"])
    sparse_results = {}
    for row in rows:
        vector = sparse_embedding.embed_query(row["query"])
        sparse_vector = SparseVector(indices=vector.indices, values=vector.values)
        sparse_results[row["id"]] = qdrant_query(
            client, params["collection_name"], sparse_vector, "omop_sparse_vector", int(params["topk"])
        )
    del sparse_embedding
    gc.collect()
    athena = RetrieverAthenaAPI(
        filters=AthenaFilters(
            vocabulary=["SNOMED", "LOINC", "UCUM", "OMOP Extension", "ATC", "RxNorm"],
            standard_concept=["Standard", "Classification"],
        ),
        k=int(params["topk"]),
    )

    llm_check = {"status": "skipped"}
    if not args.skip_llm_check:
        llm_started = time.perf_counter()
        try:
            llm = LLMManager.get_instance(params["llm_id"])
            if llm is None:
                raise RuntimeError("LLMManager returned None")
            response = llm.invoke("Reply with exactly: OK")
            llm_check = {
                "status": "passed",
                "latency_ms": round((time.perf_counter() - llm_started) * 1000, 3),
                "response_nonempty": bool(getattr(response, "content", response)),
            }
        except Exception as exc:
            llm_check = {
                "status": "failed",
                "latency_ms": round((time.perf_counter() - llm_started) * 1000, 3),
                "error": repr(exc),
            }

    records = []
    for row in rows:
        domain = row.get("domain", "all")
        athena_for_domain = athena
        athena_for_domain.k = int(params["topk"])
        total_started = time.perf_counter()
        dense_docs, dense_ms, dense_error = dense_results[row["id"]]
        sparse_docs, sparse_ms, sparse_error = sparse_results[row["id"]]
        a_docs, a_ms, a_error = invoke_athena_timed(athena_for_domain, row["query"])
        candidates = merge_candidates(
            [("qdrant_dense", dense_docs), ("qdrant_sparse", sparse_docs), ("athena", a_docs)],
            int(params["topk"]),
        )
        record = {
            **row,
            "status": "success" if candidates else "no_candidates",
            "candidates": candidates,
            "source_candidate_counts": {"qdrant_dense": len(dense_docs), "qdrant_sparse": len(sparse_docs), "athena": len(a_docs)},
            "latency_ms": {
                "qdrant_dense": dense_ms,
                "qdrant_sparse": sparse_ms,
                "athena": a_ms,
                "total": round(dense_ms + sparse_ms + (time.perf_counter() - total_started) * 1000, 3),
            },
            "errors": {key: value for key, value in {"qdrant_dense": dense_error, "qdrant_sparse": sparse_error, "athena": a_error}.items() if value},
        }
        records.append(record)

    output_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records), encoding="utf-8")
    manifest = {
        "run_id": run_id,
        "status": "completed" if all(row["status"] == "success" and not row["errors"] for row in records) and llm_check["status"] != "failed" else "completed_with_errors",
        "started_at": started_at.isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "git_commit": git_value("rev-parse", "HEAD"),
        "git_dirty": bool(git_value("status", "--porcelain", "--untracked-files=no")),
        "config_path": str(config_path),
        "config_sha256": sha256(config_path),
        "gold_path": str(gold_path),
        "gold_sha256": sha256(gold_path),
        "query_count": len(records),
        "output_path": str(output_path),
        "output_sha256": sha256(output_path),
        "llm": {"model": params["llm_id"], **llm_check},
        "retrieval": {
            "mode": params["retriever_type"],
            "embedding_model": params["embedding_model"],
            "sparse_embedding_model": params["sparse_embedding_model"],
            "qdrant_collection": params["collection_name"],
            "topk": params["topk"],
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0 if manifest["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
