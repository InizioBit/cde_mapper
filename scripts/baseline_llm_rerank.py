#!/usr/bin/env python
"""Rerank persisted Stage-0 candidates with the configured LLM."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import yaml
from dotenv import load_dotenv
from json_repair import repair_json

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def parse_order(content: str, candidate_count: int) -> list[int]:
    parsed = json.loads(repair_json(content))
    order = parsed.get("order") if isinstance(parsed, dict) else parsed
    if not isinstance(order, list):
        raise ValueError("LLM response does not contain an order list")
    normalized = []
    for value in order:
        index = int(value)
        if 1 <= index <= candidate_count and index not in normalized:
            normalized.append(index)
    normalized.extend(index for index in range(1, candidate_count + 1) if index not in normalized)
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/baseline.yaml")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    os.chdir(REPO_ROOT)
    load_dotenv(REPO_ROOT / ".env")
    params = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))["default_params"]
    from rag.manager import LLMManager

    llm = LLMManager.get_instance(params["llm_id"])
    if llm is None:
        raise RuntimeError("LLMManager returned None")
    rows = [json.loads(line) for line in Path(args.input).read_text(encoding="utf-8").splitlines() if line.strip()]
    output_rows = []
    for row in rows:
        candidates = row.get("candidates", [])
        compact = [
            {"index": index, "label": item["label"], "domain": item.get("domain"), "vocabulary": item.get("vocabulary")}
            for index, item in enumerate(candidates, 1)
        ]
        prompt = (
            "You rerank clinical terminology candidates. Return JSON only as "
            '{"order":[candidate indices from most to least relevant]}. '
            f"Query: {row['query']}\nExpected domain: {row.get('domain', 'all')}\nCandidates: {json.dumps(compact)}"
        )
        started = time.perf_counter()
        try:
            response = llm.invoke(prompt)
            order = parse_order(str(response.content), len(candidates))
            reranked = [dict(candidates[index - 1], rank=rank) for rank, index in enumerate(order, 1)]
            rerank = {"status": "success", "latency_ms": round((time.perf_counter() - started) * 1000, 3)}
        except Exception as exc:
            reranked = candidates
            rerank = {"status": "failed", "latency_ms": round((time.perf_counter() - started) * 1000, 3), "error": repr(exc)}
        output_rows.append({**row, "retrieval_candidates": candidates, "candidates": reranked, "llm_rerank": {"model": params["llm_id"], **rerank}})
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in output_rows), encoding="utf-8")
    failures = sum(row["llm_rerank"]["status"] != "success" for row in output_rows)
    summary = {"model": params["llm_id"], "query_count": len(output_rows), "failures": failures, "output": str(output)}
    print(json.dumps(summary, indent=2))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
