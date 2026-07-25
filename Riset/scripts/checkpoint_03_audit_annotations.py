"""Audit anotasi independen Checkpoint 3 dan susun daftar disagreement.

Skrip ini tidak membuat label gold secara otomatis. Status ``ready_for_adjudication``
hanya diberikan setelah kedua anotator menyelesaikan seluruh paket dan semua
dokumen lolos validasi skema. Gold set baru sah setelah adjudikasi klinis.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rag.id_entity_schema import ClinicalExtractionDocument  # noqa: E402


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: JSON tidak valid: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: setiap baris harus object")
            rows.append(value)
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def index_unique(rows: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        task_id = row.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError(f"{label}: task_id kosong/tidak valid")
        if task_id in result:
            raise ValueError(f"{label}: task_id duplikat: {task_id}")
        result[task_id] = row
    return result


def entity_key(entity: dict[str, Any]) -> tuple[Any, ...]:
    return (
        entity.get("start_char"),
        entity.get("end_char"),
        entity.get("entity_type"),
    )


ATTRIBUTE_FIELDS = (
    "normalized_mention",
    "base_entity",
    "domain",
    "value",
    "unit",
    "dose",
    "frequency",
    "route",
    "assertion",
    "temporal",
    "experiencer",
    "sentence_id",
    "epistemic_status",
)


def compare_document(
    task_id: str,
    source_field: str,
    row_a: dict[str, Any],
    row_b: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    entities_a = row_a.get("entities", [])
    entities_b = row_b.get("entities", [])
    map_a = {entity_key(entity): entity for entity in entities_a}
    map_b = {entity_key(entity): entity for entity in entities_b}
    keys_a, keys_b = set(map_a), set(map_b)
    matched = keys_a & keys_b
    denominator = len(keys_a) + len(keys_b)
    exact_f1 = 1.0 if denominator == 0 else (2 * len(matched)) / denominator

    disagreements: list[dict[str, Any]] = []
    for key in sorted(keys_a - keys_b, key=str):
        disagreements.append(
            {
                "task_id": task_id,
                "source_field": source_field,
                "kind": "entity_only_annotator_a",
                "entity_key": list(key),
                "annotator_a": map_a[key],
                "annotator_b": None,
            }
        )
    for key in sorted(keys_b - keys_a, key=str):
        disagreements.append(
            {
                "task_id": task_id,
                "source_field": source_field,
                "kind": "entity_only_annotator_b",
                "entity_key": list(key),
                "annotator_a": None,
                "annotator_b": map_b[key],
            }
        )

    attribute_matches: Counter[str] = Counter()
    attribute_totals: Counter[str] = Counter()
    for key in sorted(matched, key=str):
        differences: dict[str, dict[str, Any]] = {}
        for field in ATTRIBUTE_FIELDS:
            attribute_totals[field] += 1
            if map_a[key].get(field) == map_b[key].get(field):
                attribute_matches[field] += 1
            else:
                differences[field] = {
                    "annotator_a": map_a[key].get(field),
                    "annotator_b": map_b[key].get(field),
                }
        if differences:
            disagreements.append(
                {
                    "task_id": task_id,
                    "source_field": source_field,
                    "kind": "attribute_mismatch",
                    "entity_key": list(key),
                    "mention": map_a[key].get("mention"),
                    "differences": differences,
                }
            )

    return (
        {
            "annotator_a_entities": len(keys_a),
            "annotator_b_entities": len(keys_b),
            "matched_span_type": len(matched),
            "exact_span_type_f1": round(exact_f1, 6),
            "attribute_matches": dict(attribute_matches),
            "attribute_totals": dict(attribute_totals),
        },
        disagreements,
    )


def audit(
    tasks: list[dict[str, Any]],
    rows_a: list[dict[str, Any]],
    rows_b: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    structural_errors: list[str] = []
    schema_errors: list[dict[str, Any]] = []
    task_index = index_unique(tasks, "tasks")
    a_index = index_unique(rows_a, "annotator_a")
    b_index = index_unique(rows_b, "annotator_b")
    expected = set(task_index)

    for label, index in (("annotator_a", a_index), ("annotator_b", b_index)):
        missing = sorted(expected - set(index))
        extra = sorted(set(index) - expected)
        if missing:
            structural_errors.append(f"{label}: task hilang: {missing}")
        if extra:
            structural_errors.append(f"{label}: task tidak dikenal: {extra}")

    completion = {"annotator_a": 0, "annotator_b": 0, "both": 0}
    comparable_tasks = 0
    document_metrics: list[dict[str, Any]] = []
    disagreements: list[dict[str, Any]] = []

    for task_id in sorted(expected):
        task = task_index[task_id]
        row_a, row_b = a_index.get(task_id), b_index.get(task_id)
        if row_a is None or row_b is None:
            continue
        for label, row in (("annotator_a", row_a), ("annotator_b", row_b)):
            if row.get("parent_record_id") != task.get("parent_record_id"):
                structural_errors.append(f"{label}/{task_id}: parent_record_id berbeda")
            for field in ("question", "answer"):
                if row.get(field, {}).get("document_id") != task.get(field, {}).get(
                    "document_id"
                ):
                    structural_errors.append(
                        f"{label}/{task_id}/{field}: document_id berbeda"
                    )

        complete_a = row_a.get("annotation_meta", {}).get("status") == "complete"
        complete_b = row_b.get("annotation_meta", {}).get("status") == "complete"
        completion["annotator_a"] += int(complete_a)
        completion["annotator_b"] += int(complete_b)
        completion["both"] += int(complete_a and complete_b)

        if not (complete_a and complete_b):
            continue

        valid = True
        for label, row in (("annotator_a", row_a), ("annotator_b", row_b)):
            for field in ("question", "answer"):
                try:
                    ClinicalExtractionDocument.model_validate(row[field])
                except (ValidationError, KeyError, TypeError) as exc:
                    valid = False
                    schema_errors.append(
                        {
                            "task_id": task_id,
                            "annotator": label,
                            "source_field": field,
                            "error": str(exc),
                        }
                    )
        if not valid:
            continue

        comparable_tasks += 1
        for field in ("question", "answer"):
            metric, field_disagreements = compare_document(
                task_id, field, row_a[field], row_b[field]
            )
            metric.update({"task_id": task_id, "source_field": field})
            document_metrics.append(metric)
            disagreements.extend(field_disagreements)

    total_documents = len(document_metrics)
    total_a = sum(item["annotator_a_entities"] for item in document_metrics)
    total_b = sum(item["annotator_b_entities"] for item in document_metrics)
    total_matched = sum(item["matched_span_type"] for item in document_metrics)
    micro_denominator = total_a + total_b
    micro_f1 = (
        1.0 if micro_denominator == 0 else (2 * total_matched) / micro_denominator
    )
    macro_f1 = (
        sum(item["exact_span_type_f1"] for item in document_metrics) / total_documents
        if total_documents
        else None
    )
    attr_match: Counter[str] = Counter()
    attr_total: Counter[str] = Counter()
    for item in document_metrics:
        attr_match.update(item["attribute_matches"])
        attr_total.update(item["attribute_totals"])
    attribute_agreement = {
        field: (
            round(attr_match[field] / attr_total[field], 6)
            if attr_total[field]
            else None
        )
        for field in ATTRIBUTE_FIELDS
    }

    all_complete = completion["both"] == len(expected) and bool(expected)
    if structural_errors or schema_errors:
        status = "failed_validation"
    elif all_complete:
        status = "ready_for_adjudication"
    else:
        status = "pending_annotation"

    report = {
        "checkpoint": "Milestone A - Checkpoint 3",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "gold_status": "not_created_pending_clinical_adjudication",
        "task_counts": {
            "expected": len(expected),
            "annotator_a_rows": len(rows_a),
            "annotator_b_rows": len(rows_b),
            "completed_annotator_a": completion["annotator_a"],
            "completed_annotator_b": completion["annotator_b"],
            "completed_by_both": completion["both"],
            "valid_comparable_tasks": comparable_tasks,
        },
        "agreement": {
            "entity_key": ["start_char", "end_char", "entity_type"],
            "micro_exact_span_type_f1": (
                round(micro_f1, 6) if total_documents else None
            ),
            "macro_exact_span_type_f1": (
                round(macro_f1, 6) if macro_f1 is not None else None
            ),
            "attribute_agreement_on_matched_entities": attribute_agreement,
            "disagreement_records": len(disagreements),
        },
        "structural_errors": structural_errors,
        "schema_errors": schema_errors,
        "next_action": (
            "Isi kedua berkas anotator secara independen dan ubah status menjadi complete."
            if status == "pending_annotation"
            else "Lakukan adjudikasi klinis atas disagreement; jangan menyalin label mayoritas secara otomatis."
            if status == "ready_for_adjudication"
            else "Perbaiki error struktur/skema sebelum melanjutkan."
        ),
    }
    return report, disagreements


def parse_args() -> argparse.Namespace:
    base = REPO_ROOT / "Riset" / "Tahap_2" / "checkpoint_03"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, default=base / "stage2_annotation_tasks.jsonl")
    parser.add_argument("--annotator-a", type=Path, default=base / "stage2_annotator_a.jsonl")
    parser.add_argument("--annotator-b", type=Path, default=base / "stage2_annotator_b.jsonl")
    parser.add_argument(
        "--disagreements", type=Path, default=base / "stage2_annotation_disagreement.jsonl"
    )
    parser.add_argument("--audit", type=Path, default=base / "stage2_checkpoint_03_audit.json")
    parser.add_argument(
        "--statistics", type=Path, default=base / "stage2_gold_statistics.json"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report, disagreements = audit(
        read_jsonl(args.tasks),
        read_jsonl(args.annotator_a),
        read_jsonl(args.annotator_b),
    )
    write_jsonl(args.disagreements, disagreements)
    write_json(args.audit, report)
    write_json(
        args.statistics,
        {
            "status": report["status"],
            "gold_status": report["gold_status"],
            "task_counts": report["task_counts"],
            "agreement": report["agreement"],
            "note": "Statistik final diperbarui setelah adjudikasi dan pembekuan gold v1.",
        },
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["status"] == "failed_validation" else 0


if __name__ == "__main__":
    raise SystemExit(main())
