from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rag.id_preprocess import IndonesianClinicalNormalizer


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            row["_line"] = line_number
            rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Indonesian clinical normalization.")
    parser.add_argument("--gold-file", default="data/gold/id_normalization_gold.jsonl")
    parser.add_argument("--resource-dir", default="data/input")
    parser.add_argument("--output-file", default="Riset/id_preprocess_audit_result.json")
    args = parser.parse_args()

    started = time.perf_counter()
    gold_file = Path(args.gold_file)
    output_file = Path(args.output_file)

    normalizer = IndonesianClinicalNormalizer.from_resource_dir(args.resource_dir)
    rows = read_jsonl(gold_file)

    cases: list[dict] = []
    replacement_totals = {"typo": 0, "abbreviation": 0, "unit": 0}
    exact_matches = 0
    changed = 0

    for row in rows:
        result = normalizer.normalize(row["input"], audit=True)
        is_exact = result.normalized_text == row["expected"]
        exact_matches += int(is_exact)
        changed += int(result.normalized_text != row["input"])
        for key in replacement_totals:
            replacement_totals[key] += result.replacements.get(key, 0)
        cases.append(
            {
                "id": row["id"],
                "input": row["input"],
                "expected": row["expected"],
                "actual": result.normalized_text,
                "exact": is_exact,
                "focus": row.get("focus", []),
                "replacements": result.replacements,
                "steps": [step.__dict__ for step in result.steps],
            }
        )

    total = len(rows)
    payload = {
        "ok": exact_matches == total,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "duration_seconds": round(time.perf_counter() - started, 4),
        "gold_file": str(gold_file),
        "resource_dir": args.resource_dir,
        "total_cases": total,
        "exact_matches": exact_matches,
        "exact_normalized_match": round(exact_matches / total, 4) if total else 0.0,
        "changed_cases": changed,
        "replacement_totals": replacement_totals,
        "cases": cases,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
