#!/usr/bin/env python
"""Compute Stage-0 retrieval metrics from a persisted experiment artifact."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError(f"Experiment output is empty: {path}")
    return rows


def relevant(candidate: dict, gold: set[str]) -> bool:
    return bool({str(value).casefold() for value in candidate.get("identifiers", [])} & gold)


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * p
    lower, upper = math.floor(index), math.ceil(index)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - index) + ordered[upper] * (index - lower)


def evaluate(rows: list[dict], ks: tuple[int, ...] = (1, 3, 5, 10)) -> dict:
    totals = {k: {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "ndcg": 0.0} for k in ks}
    reciprocal_ranks = []
    latency = []
    successful = 0
    errors = 0
    for row in rows:
        candidates = row.get("candidates", [])
        gold = {str(value).casefold() for value in row.get("gold_ids", [])}
        flags = [relevant(candidate, gold) for candidate in candidates]
        successful += int(bool(candidates))
        errors += int(bool(row.get("errors")))
        total_latency = float(row.get("latency_ms", {}).get("total", 0.0))
        total_latency += float(row.get("llm_rerank", {}).get("latency_ms", 0.0))
        latency.append(total_latency)
        first_rank = next((index + 1 for index, flag in enumerate(flags) if flag), None)
        reciprocal_ranks.append(1.0 / first_rank if first_rank else 0.0)
        relevant_total = max(1, len(gold))
        # gold_ids may contain equivalent OMOP and vocabulary identifiers for one concept.
        if len(gold) > 1:
            relevant_total = 1
        for k in ks:
            hits = sum(flags[:k])
            totals[k]["accuracy"] += float(hits > 0)
            totals[k]["precision"] += hits / k
            totals[k]["recall"] += min(1.0, hits / relevant_total)
            dcg = sum(1.0 / math.log2(rank + 2) for rank, flag in enumerate(flags[:k]) if flag)
            totals[k]["ndcg"] += min(1.0, dcg)  # ideal DCG is 1 for one target concept

    count = len(rows)
    metrics = {
        "query_count": count,
        "coverage": successful / count,
        "query_failure_rate": (count - successful) / count,
        "partial_source_error_rate": errors / count,
        "mrr": statistics.fmean(reciprocal_ranks),
        "latency_ms": {
            "mean": statistics.fmean(latency),
            "p50": percentile(latency, 0.50),
            "p95": percentile(latency, 0.95),
            "max": max(latency),
        },
    }
    for k in ks:
        metrics[f"accuracy@{k}"] = totals[k]["accuracy"] / count
        metrics[f"precision@{k}"] = totals[k]["precision"] / count
        metrics[f"recall@{k}"] = totals[k]["recall"] / count
        metrics[f"ndcg@{k}"] = totals[k]["ndcg"] / count
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="Riset/baseline_metrics.json")
    args = parser.parse_args()
    input_path = Path(args.input)
    metrics = {"input": str(input_path), **evaluate(read_jsonl(input_path))}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
