#!/usr/bin/env python
"""Online Stage-0 integration checks for Qdrant, Athena, and Together LLM."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import yaml
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def check(name, function) -> dict:
    started = time.perf_counter()
    try:
        detail = function()
        return {"check": name, "status": "passed", "latency_ms": round((time.perf_counter() - started) * 1000, 3), "detail": detail}
    except Exception as exc:
        return {"check": name, "status": "failed", "latency_ms": round((time.perf_counter() - started) * 1000, 3), "error": repr(exc)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/baseline.yaml")
    parser.add_argument("--output", default="Riset/baseline_integration_audit.json")
    args = parser.parse_args()
    os.chdir(REPO_ROOT)
    load_dotenv(REPO_ROOT / ".env")
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))["default_params"]

    from qdrant_client import QdrantClient
    from rag.athena_api_retriever import AthenaFilters, RetrieverAthenaAPI
    from rag.manager import LLMManager

    checks = []
    checks.append(check("together_key_present", lambda: "TOGETHER_API_KEY is set" if os.getenv("TOGETHER_API_KEY") else (_ for _ in ()).throw(RuntimeError("TOGETHER_API_KEY is not set"))))

    def qdrant_check():
        client = QdrantClient(url=config["qdrant_url"], port=int(config["qdrant_port"]), https=True, timeout=60)
        if not client.collection_exists(config["collection_name"]):
            raise RuntimeError(f"Collection not found: {config['collection_name']}")
        info = client.get_collection(config["collection_name"])
        return {"collection": config["collection_name"], "points_count": info.points_count}

    checks.append(check("qdrant_collection", qdrant_check))

    def athena_check():
        retriever = RetrieverAthenaAPI(filters=AthenaFilters(vocabulary=["SNOMED", "LOINC"]), k=3)
        docs = retriever.invoke("diabetes mellitus")
        if not docs:
            raise RuntimeError("Athena returned no candidates")
        return {"candidate_count": len(docs), "fields_present": all("sid" in doc.metadata and "label" in doc.metadata for doc in docs)}

    checks.append(check("athena_retrieval", athena_check))

    def llm_check():
        llm = LLMManager.get_instance(config["llm_id"])
        if llm is None:
            raise RuntimeError("LLMManager returned None")
        response = llm.invoke("Reply with exactly: OK")
        if not getattr(response, "content", response):
            raise RuntimeError("Together returned an empty response")
        return {"model": config["llm_id"], "response_nonempty": True}

    checks.append(check("together_llm", llm_check))
    payload = {"ok": all(item["status"] == "passed" for item in checks), "checks": checks}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
