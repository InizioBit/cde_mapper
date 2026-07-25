"""Milestone A, Checkpoint 2: validate entity schema and annotation examples."""

from __future__ import annotations

import argparse
import copy
import hashlib
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

from rag.id_entity_schema import (  # noqa: E402
    ClinicalExtractionDocument,
    EntityType,
    Stage2InputDocument,
)


CHECKPOINT_NAME = "milestone_a_checkpoint_02"
SCHEMA_VERSION = "1.0.0"
CORE_ENTITY_TYPES = {entity_type.value for entity_type in EntityType} - {"other"}
REQUIRED_GUIDELINE_SECTIONS = {
    "## 2. Prinsip Umum",
    "## 4. Batas Entity Span",
    "## 5. Entity Type",
    "## 8. Assertion",
    "## 9. Temporal",
    "## 10. Experiencer",
    "## 11. Speaker dan Source",
    "## 12. Epistemic Status",
    "## 13. Offset dan Evidence",
    "## 17. Kasus Answer",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} must contain a JSON object")
            rows.append(value)
    return rows


def set_path(payload: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    target: Any = payload
    for part in parts[:-1]:
        target = target[int(part)] if isinstance(target, list) else target[part]
    final = parts[-1]
    if isinstance(target, list):
        target[int(final)] = value
    else:
        target[final] = value


def validate_checkpoint_01(
    path: Path,
) -> tuple[int, list[dict[str, Any]], Counter[str]]:
    failures: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for line_number, payload in enumerate(read_jsonl(path), start=1):
        try:
            document = Stage2InputDocument.model_validate(payload)
            counts[f"source:{document.source_field}"] += 1
            counts[f"speaker:{document.speaker}"] += 1
        except ValidationError as error:
            failures.append(
                {
                    "line": line_number,
                    "document_id": payload.get("document_id"),
                    "errors": error.errors(include_url=False),
                }
            )
    return sum(counts[key] for key in counts if key.startswith("source:")), failures, counts


def validate_positive_examples(
    path: Path,
) -> tuple[
    dict[str, dict[str, Any]],
    list[dict[str, Any]],
    Counter[str],
]:
    examples: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, Any]] = []
    coverage: Counter[str] = Counter()
    for line_number, raw_payload in enumerate(read_jsonl(path), start=1):
        example_id = raw_payload.get("example_id")
        if not isinstance(example_id, str) or not example_id:
            failures.append(
                {"line": line_number, "errors": [{"msg": "missing example_id"}]}
            )
            continue
        if example_id in examples:
            failures.append(
                {
                    "line": line_number,
                    "example_id": example_id,
                    "errors": [{"msg": "duplicate example_id"}],
                }
            )
            continue
        payload = {key: value for key, value in raw_payload.items() if key != "example_id"}
        examples[example_id] = payload
        try:
            document = ClinicalExtractionDocument.model_validate(payload)
            coverage[f"source:{document.source_field}"] += 1
            coverage[f"speaker:{document.speaker}"] += 1
            for entity in document.entities:
                coverage[f"entity_type:{entity.entity_type}"] += 1
                coverage[f"assertion:{entity.assertion}"] += 1
                coverage[f"temporal:{entity.temporal}"] += 1
                coverage[f"experiencer:{entity.experiencer}"] += 1
                coverage[f"epistemic:{entity.epistemic_status}"] += 1
        except ValidationError as error:
            failures.append(
                {
                    "line": line_number,
                    "example_id": example_id,
                    "errors": error.errors(include_url=False),
                }
            )
    return examples, failures, coverage


def validate_negative_examples(
    path: Path,
    positive_examples: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cases = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cases, list):
        raise ValueError("Invalid examples file must contain a JSON array")
    passed: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for case in cases:
        case_id = case.get("case_id")
        base_example_id = case.get("base_example_id")
        if base_example_id not in positive_examples:
            failures.append(
                {
                    "case_id": case_id,
                    "reason": f"unknown base_example_id: {base_example_id}",
                }
            )
            continue
        payload = copy.deepcopy(positive_examples[base_example_id])
        set_path(payload, case["path"], case.get("value"))
        try:
            ClinicalExtractionDocument.model_validate(payload)
            failures.append(
                {
                    "case_id": case_id,
                    "reason": "invalid payload was accepted",
                }
            )
        except ValidationError as error:
            error_text = str(error)
            expected_error = str(case.get("expected_error", ""))
            if expected_error.casefold() not in error_text.casefold():
                failures.append(
                    {
                        "case_id": case_id,
                        "reason": "validation failed with unexpected error",
                        "expected_error": expected_error,
                        "actual_error": error_text,
                    }
                )
            else:
                passed.append(
                    {
                        "case_id": case_id,
                        "expected_error": expected_error,
                    }
                )
    return passed, failures


def validate_guideline(path: Path) -> tuple[list[str], dict[str, int]]:
    text = path.read_text(encoding="utf-8")
    missing = sorted(
        section for section in REQUIRED_GUIDELINE_SECTIONS if section not in text
    )
    statistics = {
        "characters": len(text),
        "lines": len(text.splitlines()),
        "level_2_sections": sum(
            line.startswith("## ") for line in text.splitlines()
        ),
    }
    return missing, statistics


def write_schema(path: Path, schema: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Milestone A Checkpoint 2 entity contracts."
    )
    parser.add_argument(
        "--checkpoint-01-input",
        default="Riset/Tahap_2/checkpoint_01/stage2_checkpoint_01_input.jsonl",
    )
    parser.add_argument(
        "--examples-file",
        default="Riset/Tahap_2/checkpoint_02/stage2_schema_examples.jsonl",
    )
    parser.add_argument(
        "--invalid-examples-file",
        default="Riset/Tahap_2/checkpoint_02/stage2_schema_invalid_examples.json",
    )
    parser.add_argument(
        "--guideline-file",
        default="Riset/Tahap_2/checkpoint_02/stage2_annotation_guideline.md",
    )
    parser.add_argument(
        "--input-schema-file",
        default="Riset/Tahap_2/checkpoint_02/stage2_input_document_schema.json",
    )
    parser.add_argument(
        "--entity-schema-file",
        default="Riset/Tahap_2/checkpoint_02/stage2_entity_extraction_schema.json",
    )
    parser.add_argument(
        "--audit-file",
        default="Riset/Tahap_2/checkpoint_02/stage2_checkpoint_02_audit.json",
    )
    args = parser.parse_args()

    checkpoint_01_path = Path(args.checkpoint_01_input)
    examples_path = Path(args.examples_file)
    invalid_examples_path = Path(args.invalid_examples_file)
    guideline_path = Path(args.guideline_file)
    input_schema_path = Path(args.input_schema_file)
    entity_schema_path = Path(args.entity_schema_file)
    audit_path = Path(args.audit_file)

    required_files = [
        checkpoint_01_path,
        examples_path,
        invalid_examples_path,
        guideline_path,
    ]
    missing_files = [str(path) for path in required_files if not path.exists()]
    if missing_files:
        raise FileNotFoundError(f"Required files not found: {missing_files}")

    checkpoint_01_valid, checkpoint_01_failures, checkpoint_01_counts = (
        validate_checkpoint_01(checkpoint_01_path)
    )
    positive_examples, positive_failures, coverage = validate_positive_examples(
        examples_path
    )
    negative_passed, negative_failures = validate_negative_examples(
        invalid_examples_path, positive_examples
    )
    missing_guideline_sections, guideline_statistics = validate_guideline(
        guideline_path
    )

    write_schema(
        input_schema_path,
        Stage2InputDocument.model_json_schema(mode="validation"),
    )
    write_schema(
        entity_schema_path,
        ClinicalExtractionDocument.model_json_schema(mode="validation"),
    )

    covered_entity_types = {
        key.removeprefix("entity_type:")
        for key in coverage
        if key.startswith("entity_type:") and coverage[key] > 0
    }
    missing_core_entity_types = sorted(CORE_ENTITY_TYPES - covered_entity_types)
    source_coverage = {
        key.removeprefix("source:")
        for key in coverage
        if key.startswith("source:") and coverage[key] > 0
    }
    assertion_coverage = {
        key.removeprefix("assertion:")
        for key in coverage
        if key.startswith("assertion:") and coverage[key] > 0
    }
    experiencer_coverage = {
        key.removeprefix("experiencer:")
        for key in coverage
        if key.startswith("experiencer:") and coverage[key] > 0
    }

    invalid_case_count = len(json.loads(invalid_examples_path.read_text(encoding="utf-8")))
    exit_criteria = {
        "checkpoint_01_all_documents_valid": (
            checkpoint_01_valid == 300 and not checkpoint_01_failures
        ),
        "positive_examples_available": len(positive_examples) >= 8,
        "all_positive_examples_valid": not positive_failures,
        "all_negative_examples_rejected": (
            len(negative_passed) == invalid_case_count and not negative_failures
        ),
        "core_entity_types_covered": not missing_core_entity_types,
        "question_and_answer_examples_available": source_coverage
        == {"question", "answer"},
        "assertion_examples_cover_context": {
            "present",
            "negated",
            "uncertain",
            "hypothetical",
        }.issubset(assertion_coverage),
        "experiencer_examples_cover_patient_and_family": {
            "patient",
            "family",
        }.issubset(experiencer_coverage),
        "guideline_required_sections_available": not missing_guideline_sections,
        "json_schemas_exported": input_schema_path.exists()
        and entity_schema_path.exists(),
    }

    audit_payload = {
        "checkpoint": CHECKPOINT_NAME,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if all(exit_criteria.values()) else "fail",
        "inputs": {
            "checkpoint_01": {
                "path": str(checkpoint_01_path),
                "sha256": sha256_file(checkpoint_01_path),
            },
            "examples": {
                "path": str(examples_path),
                "sha256": sha256_file(examples_path),
            },
            "invalid_examples": {
                "path": str(invalid_examples_path),
                "sha256": sha256_file(invalid_examples_path),
            },
            "guideline": {
                "path": str(guideline_path),
                "sha256": sha256_file(guideline_path),
            },
        },
        "outputs": {
            "input_schema": {
                "path": str(input_schema_path),
                "sha256": sha256_file(input_schema_path),
            },
            "entity_schema": {
                "path": str(entity_schema_path),
                "sha256": sha256_file(entity_schema_path),
            },
        },
        "checkpoint_01_validation": {
            "valid_documents": checkpoint_01_valid,
            "counts": dict(sorted(checkpoint_01_counts.items())),
            "failures": checkpoint_01_failures,
        },
        "positive_examples": {
            "total": len(positive_examples),
            "failures": positive_failures,
        },
        "negative_examples": {
            "total": invalid_case_count,
            "correctly_rejected": len(negative_passed),
            "passed_cases": negative_passed,
            "failures": negative_failures,
        },
        "coverage": {
            "counts": dict(sorted(coverage.items())),
            "covered_entity_types": sorted(covered_entity_types),
            "missing_core_entity_types": missing_core_entity_types,
            "source_fields": sorted(source_coverage),
            "assertions": sorted(assertion_coverage),
            "experiencers": sorted(experiencer_coverage),
        },
        "guideline": {
            **guideline_statistics,
            "missing_required_sections": missing_guideline_sections,
        },
        "exit_criteria": exit_criteria,
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(
        json.dumps(audit_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    summary = {
        "status": audit_payload["status"],
        "checkpoint_01_valid_documents": checkpoint_01_valid,
        "positive_examples": len(positive_examples),
        "negative_examples_rejected": len(negative_passed),
        "covered_entity_types": len(covered_entity_types),
        "missing_core_entity_types": missing_core_entity_types,
        "audit_file": str(audit_path),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if audit_payload["status"] == "pass" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        print(f"Checkpoint 2 failed: {error}", file=sys.stderr)
        raise SystemExit(2)
