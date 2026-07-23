"""Normalize Alodokter question-answer data and save an auditable artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rag.id_preprocess import IndonesianClinicalNormalizer


def _result_payload(result) -> dict:
    return {
        "raw_text": result.original_text,
        "normalized_text": result.normalized_text,
        "content_text": result.content_text,
        "sentences": result.sentences,
        "normalization_changes": [change.__dict__ for change in result.changes],
        "warnings": result.warnings,
        "boilerplate": result.boilerplate,
        "replacements": result.replacements,
        "profile": result.profile,
        "normalizer_version": result.normalizer_version,
        "resource_version": result.resource_version,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize question and answer fields in Alodokter crawl data."
    )
    parser.add_argument(
        "--input-file",
        default="Riset/crawler_alodokter/hasil_crawl_alodokter_qa_pairs.json",
    )
    parser.add_argument(
        "--output-file",
        default="Riset/crawler_alodokter/hasil_normalisasi_tahap_1.jsonl",
    )
    parser.add_argument("--resource-dir", default="data/input")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    output_path = Path(args.output_file)
    rows = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("Alodokter input must contain a JSON array.")

    normalizer = IndonesianClinicalNormalizer.from_resource_dir(args.resource_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    totals = {
        "records": 0,
        "question_changes": 0,
        "answer_changes": 0,
        "warnings": 0,
    }
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for index, row in enumerate(rows, start=1):
            question = row.get("question") or {}
            answer = row.get("answer") or {}
            question_text = question.get("raw_text") or question.get("clean_text") or ""
            answer_text = answer.get("raw_text") or answer.get("clean_text") or ""
            question_result = normalizer.normalize(
                question_text, audit=True, profile="question"
            )
            answer_result = normalizer.normalize(
                answer_text, audit=True, profile="answer"
            )
            record_id = hashlib.sha256(
                str(row.get("url") or index).encode("utf-8")
            ).hexdigest()[:16]
            payload = {
                "record_id": record_id,
                "source": row.get("source"),
                "url": row.get("url"),
                "title": row.get("title"),
                "question": _result_payload(question_result),
                "answer": _result_payload(answer_result),
            }
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
            totals["records"] += 1
            totals["question_changes"] += len(question_result.changes)
            totals["answer_changes"] += len(answer_result.changes)
            totals["warnings"] += len(question_result.warnings)
            totals["warnings"] += len(answer_result.warnings)

    print(json.dumps({"ok": True, "output_file": str(output_path), **totals}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
