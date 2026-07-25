"""Milestone A, Checkpoint 1: prepare Stage 2 input and audit provenance.

This script converts every normalized Stage 1 consultation record into two
independent Stage 2 documents:

* question -> patient
* answer   -> doctor

The implementation uses only the Python standard library. It accepts JSONL or
JSON-array input and writes a deterministic JSONL document artifact plus a JSON
audit report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


CHECKPOINT_NAME = "milestone_a_checkpoint_01"
SCHEMA_VERSION = "1.0.0"
SOURCE_SPEAKER = {
    "question": "patient",
    "answer": "doctor",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def read_records(path: Path) -> list[dict[str, Any]]:
    """Read either a JSON array or one-JSON-object-per-line JSONL file."""
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    if path.suffix.casefold() == ".json":
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, list):
            raise ValueError("JSON input must contain an array of records.")
        records = value
    else:
        records = []
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(
                        f"JSONL line {line_number} must contain a JSON object."
                    )
                records.append(value)

    if not all(isinstance(record, dict) for record in records):
        raise ValueError("Every input record must be a JSON object.")
    return records


def sentences_are_traceable(normalized_text: str, sentences: Iterable[str]) -> bool:
    """Return True when sentences occur in source order in normalized_text."""
    cursor = 0
    for sentence in sentences:
        if not isinstance(sentence, str) or not sentence.strip():
            return False
        position = normalized_text.find(sentence, cursor)
        if position < 0:
            return False
        cursor = position + len(sentence)
    return True


def build_document(
    record: dict[str, Any],
    source_field: str,
    input_index: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    parent_record_id = record.get("record_id")
    if not isinstance(parent_record_id, str) or not parent_record_id.strip():
        parent_record_id = f"missing-record-{input_index:06d}"
        issues.append(
            {
                "code": "missing_parent_record_id",
                "input_index": input_index,
                "source_field": source_field,
            }
        )

    section = record.get(source_field)
    if not isinstance(section, dict):
        section = {}
        issues.append(
            {
                "code": "missing_source_section",
                "input_index": input_index,
                "parent_record_id": parent_record_id,
                "source_field": source_field,
            }
        )

    raw_text = section.get("raw_text")
    normalized_text = section.get("normalized_text")
    sentences = section.get("sentences")
    if not isinstance(raw_text, str) or not raw_text.strip():
        issues.append(
            {
                "code": "missing_raw_text",
                "parent_record_id": parent_record_id,
                "source_field": source_field,
            }
        )
        raw_text = "" if raw_text is None else str(raw_text)
    if not isinstance(normalized_text, str) or not normalized_text.strip():
        issues.append(
            {
                "code": "missing_normalized_text",
                "parent_record_id": parent_record_id,
                "source_field": source_field,
            }
        )
        normalized_text = "" if normalized_text is None else str(normalized_text)
    if not isinstance(sentences, list):
        issues.append(
            {
                "code": "invalid_sentences",
                "parent_record_id": parent_record_id,
                "source_field": source_field,
            }
        )
        sentences = []

    expected_profile = source_field
    profile = section.get("profile")
    if profile != expected_profile:
        issues.append(
            {
                "code": "profile_mismatch",
                "parent_record_id": parent_record_id,
                "source_field": source_field,
                "expected": expected_profile,
                "actual": profile,
            }
        )

    if normalized_text and sentences and not sentences_are_traceable(
        normalized_text, sentences
    ):
        issues.append(
            {
                "code": "sentence_order_not_traceable",
                "parent_record_id": parent_record_id,
                "source_field": source_field,
            }
        )

    document_id = f"{parent_record_id}-{source_field}"
    document = {
        "document_id": document_id,
        "parent_record_id": parent_record_id,
        "source_field": source_field,
        "speaker": SOURCE_SPEAKER[source_field],
        "raw_text": raw_text,
        "normalized_text": normalized_text,
        "sentences": sentences,
        "sentence_count": len(sentences),
        "source": record.get("source"),
        "url": record.get("url"),
        "title": record.get("title"),
        "normalization_profile": profile,
        "normalizer_version": section.get("normalizer_version"),
        "resource_version": section.get("resource_version"),
        "normalization_warnings": section.get("warnings", []),
        "provenance": {
            "input_index": input_index,
            "stage": "stage_1_normalization",
            "raw_text_sha256": sha256_text(raw_text),
            "normalized_text_sha256": sha256_text(normalized_text),
        },
        "schema_version": SCHEMA_VERSION,
    }
    return document, issues


def validate_collection(
    records: list[dict[str, Any]],
    documents: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    expected_records: int | None,
) -> dict[str, Any]:
    document_ids = [document["document_id"] for document in documents]
    parent_counts = Counter(document["parent_record_id"] for document in documents)
    source_counts = Counter(document["source_field"] for document in documents)
    speaker_counts = Counter(document["speaker"] for document in documents)
    issue_counts = Counter(issue["code"] for issue in issues)

    duplicate_document_ids = sorted(
        document_id
        for document_id, count in Counter(document_ids).items()
        if count > 1
    )
    invalid_parent_counts = sorted(
        parent_id for parent_id, count in parent_counts.items() if count != 2
    )
    input_record_ids = [
        record.get("record_id")
        for record in records
        if isinstance(record.get("record_id"), str) and record.get("record_id")
    ]
    duplicate_input_record_ids = sorted(
        record_id
        for record_id, count in Counter(input_record_ids).items()
        if count > 1
    )

    expected_document_count = len(records) * len(SOURCE_SPEAKER)
    exit_criteria = {
        "expected_input_record_count": (
            expected_records is None or len(records) == expected_records
        ),
        "all_records_converted": len(documents) == expected_document_count,
        "question_count_matches_input": source_counts["question"] == len(records),
        "answer_count_matches_input": source_counts["answer"] == len(records),
        "all_document_ids_unique": not duplicate_document_ids,
        "all_input_record_ids_unique": not duplicate_input_record_ids,
        "each_parent_has_question_and_answer": not invalid_parent_counts,
        "all_normalized_text_nonempty": issue_counts["missing_normalized_text"] == 0,
        "all_raw_text_available": issue_counts["missing_raw_text"] == 0,
        "all_profiles_match_source": issue_counts["profile_mismatch"] == 0,
        "all_sentences_traceable": issue_counts["sentence_order_not_traceable"] == 0,
        "all_source_sections_available": issue_counts["missing_source_section"] == 0,
    }
    return {
        "record_counts": {
            "input_records": len(records),
            "expected_input_records": expected_records,
            "output_documents": len(documents),
            "expected_output_documents": expected_document_count,
            "question_documents": source_counts["question"],
            "answer_documents": source_counts["answer"],
        },
        "speaker_counts": dict(sorted(speaker_counts.items())),
        "issue_counts": dict(sorted(issue_counts.items())),
        "duplicate_document_ids": duplicate_document_ids,
        "duplicate_input_record_ids": duplicate_input_record_ids,
        "invalid_parent_document_counts": invalid_parent_counts,
        "exit_criteria": exit_criteria,
        "passed": all(exit_criteria.values()),
    }


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return sha256_bytes(path.read_bytes())


def parse_expected_records(value: int) -> int | None:
    if value < 0:
        raise ValueError("--expected-records cannot be negative.")
    return None if value == 0 else value


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare and audit Milestone A Checkpoint 1 Stage 2 input."
    )
    parser.add_argument(
        "--input-file",
        default="Riset/crawler_alodokter/hasil_normalisasi_tahap_1.jsonl",
    )
    parser.add_argument(
        "--output-file",
        default="Riset/Tahap_2/checkpoint_01/stage2_checkpoint_01_input.jsonl",
    )
    parser.add_argument(
        "--audit-file",
        default="Riset/Tahap_2/checkpoint_01/stage2_checkpoint_01_audit.json",
    )
    parser.add_argument(
        "--expected-records",
        type=int,
        default=150,
        help="Expected Stage 1 record count; use 0 to disable this gate.",
    )
    args = parser.parse_args()

    input_path = Path(args.input_file)
    output_path = Path(args.output_file)
    audit_path = Path(args.audit_file)
    expected_records = parse_expected_records(args.expected_records)

    records = read_records(input_path)
    documents: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for input_index, record in enumerate(records, start=1):
        for source_field in SOURCE_SPEAKER:
            document, document_issues = build_document(
                record, source_field, input_index
            )
            documents.append(document)
            issues.extend(document_issues)

    validation = validate_collection(
        records, documents, issues, expected_records=expected_records
    )
    output_sha256 = write_jsonl(output_path, documents)
    audit_payload = {
        "checkpoint": CHECKPOINT_NAME,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if validation["passed"] else "fail",
        "input": {
            "path": str(input_path),
            "sha256": sha256_bytes(input_path.read_bytes()),
            "format": "json" if input_path.suffix.casefold() == ".json" else "jsonl",
        },
        "output": {
            "path": str(output_path),
            "sha256": output_sha256,
            "format": "jsonl",
        },
        **validation,
        "issues": issues,
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(
        json.dumps(audit_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    summary = {
        "status": audit_payload["status"],
        "input_records": validation["record_counts"]["input_records"],
        "output_documents": validation["record_counts"]["output_documents"],
        "question_documents": validation["record_counts"]["question_documents"],
        "answer_documents": validation["record_counts"]["answer_documents"],
        "issues": len(issues),
        "output_file": str(output_path),
        "audit_file": str(audit_path),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if validation["passed"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        print(f"Checkpoint 1 failed: {error}", file=sys.stderr)
        raise SystemExit(2)
