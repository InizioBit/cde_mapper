"""Milestone A, Checkpoint 3: prepare a deterministic gold-set annotation pack.

The script does not fabricate gold annotations. It selects representative
question-answer pairs, writes annotation tasks, and creates independent blank
templates for two annotators. Existing annotation templates are never
overwritten unless --overwrite-templates is explicitly supplied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from pydantic import ValidationError


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rag.id_entity_schema import Stage2InputDocument  # noqa: E402


CHECKPOINT_NAME = "milestone_a_checkpoint_03"
PACKAGE_VERSION = "1.0.0"
GUIDELINE_VERSION = "1.0.0"

PATTERNS = {
    "negation": re.compile(r"\b(?:tidak|tanpa|bukan|belum|tak)\b", re.I),
    "uncertainty": re.compile(
        r"\b(?:mungkin|kemungkinan|diduga|curiga|bisa jadi|dapat disebabkan)\b",
        re.I,
    ),
    "temporal": re.compile(
        r"\b(?:sejak|selama|kemarin|dulu|sebelumnya|sekarang|saat ini|"
        r"hari|minggu|bulan|tahun)\b",
        re.I,
    ),
    "drug_or_dose": re.compile(
        r"\b(?:obat|tablet|kapsul|sirup|vitamin|antibiotik|minum|dosis|"
        r"\d+(?:[.,]\d+)?\s*(?:mg|mcg|g|ml))\b",
        re.I,
    ),
    "measurement": re.compile(
        r"\b(?:tekanan darah|gula darah|hemoglobin|saturasi|suhu|hasil lab|"
        r"\d+(?:[.,]\d+)?\s*(?:mg/dl|g/dl|mmhg|%|kg|cm))\b",
        re.I,
    ),
    "family_experiencer": re.compile(
        r"\b(?:ibu|ayah|anak|bayi|suami|istri|kakak|adik|keluarga)\b",
        re.I,
    ),
    "recommendation": re.compile(
        r"\b(?:sebaiknya|disarankan|dianjurkan|periksakan|konsultasikan|"
        r"segera ke|perlu diperiksa)\b",
        re.I,
    ),
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def stable_key(seed: str, parent_record_id: str) -> str:
    return sha256_bytes(f"{seed}:{parent_record_id}".encode("utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} must contain an object")
            rows.append(value)
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def validate_and_pair(
    path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pairs: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, Any]] = []
    for line_number, payload in enumerate(read_jsonl(path), start=1):
        try:
            document = Stage2InputDocument.model_validate(payload)
        except ValidationError as error:
            failures.append(
                {
                    "line": line_number,
                    "document_id": payload.get("document_id"),
                    "errors": error.errors(include_url=False),
                }
            )
            continue
        pair = pairs.setdefault(document.parent_record_id, {})
        if document.source_field in pair:
            failures.append(
                {
                    "line": line_number,
                    "document_id": document.document_id,
                    "errors": [{"msg": "duplicate source_field for parent"}],
                }
            )
            continue
        pair[document.source_field] = payload

    complete_pairs: list[dict[str, Any]] = []
    for parent_record_id, pair in pairs.items():
        if set(pair) != {"question", "answer"}:
            failures.append(
                {
                    "parent_record_id": parent_record_id,
                    "errors": [{"msg": "question-answer pair is incomplete"}],
                }
            )
            continue
        complete_pairs.append(
            {
                "parent_record_id": parent_record_id,
                "question": pair["question"],
                "answer": pair["answer"],
            }
        )
    return complete_pairs, failures


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text, re.UNICODE))


def derive_strata(pair: dict[str, Any]) -> list[str]:
    question = pair["question"]
    answer = pair["answer"]
    question_text = question["normalized_text"]
    answer_text = answer["normalized_text"]
    combined = f"{question_text}\n{answer_text}"

    tags = [name for name, pattern in PATTERNS.items() if pattern.search(combined)]
    question_sentences = len(question["sentences"])
    answer_sentences = len(answer["sentences"])
    if question_sentences >= 8 or word_count(question_text) >= 100:
        tags.append("long_question")
    if answer_sentences >= 25 or word_count(answer_text) >= 350:
        tags.append("long_answer")
    if question_sentences >= 5 and len(tags) >= 3:
        tags.append("multi_context_question")
    return sorted(set(tags)) or ["general"]


def stratified_sample(
    pairs: list[dict[str, Any]],
    sample_size: int,
    seed: str,
) -> tuple[list[dict[str, Any]], Counter[str], Counter[str]]:
    if sample_size <= 0:
        raise ValueError("sample_size must be positive")
    if sample_size > len(pairs):
        raise ValueError("sample_size cannot exceed the available pair count")

    candidates = []
    population_counts: Counter[str] = Counter()
    for pair in pairs:
        tags = derive_strata(pair)
        population_counts.update(tags)
        candidates.append(
            {
                **pair,
                "strata": tags,
                "_stable_key": stable_key(seed, pair["parent_record_id"]),
            }
        )

    selected: list[dict[str, Any]] = []
    selected_counts: Counter[str] = Counter()
    remaining = candidates.copy()
    target_per_stratum = max(3, min(8, round(sample_size / 5)))

    while len(selected) < sample_size:
        def score(candidate: dict[str, Any]) -> tuple[float, str]:
            diversity_score = 0.0
            for tag in candidate["strata"]:
                rarity = 1.0 / max(1, population_counts[tag]) ** 0.5
                deficit = max(0, target_per_stratum - selected_counts[tag])
                diversity_score += rarity * (1.0 + deficit)
                diversity_score += 0.1 / (1 + selected_counts[tag])
            return diversity_score, candidate["_stable_key"]

        chosen = max(remaining, key=score)
        remaining.remove(chosen)
        selected.append(chosen)
        selected_counts.update(chosen["strata"])

    selected.sort(key=lambda item: item["_stable_key"])
    for sequence, item in enumerate(selected, start=1):
        item["sample_sequence"] = sequence
        item.pop("_stable_key", None)
    return selected, population_counts, selected_counts


def task_document(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "document_id": document["document_id"],
        "parent_record_id": document["parent_record_id"],
        "source_field": document["source_field"],
        "speaker": document["speaker"],
        "raw_text": document["raw_text"],
        "normalized_text": document["normalized_text"],
        "sentences": document["sentences"],
        "sentence_count": document["sentence_count"],
        "normalization_warnings": document.get("normalization_warnings", []),
    }


def extraction_template(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "document_id": document["document_id"],
        "parent_record_id": document["parent_record_id"],
        "source_field": document["source_field"],
        "speaker": document["speaker"],
        "normalized_text": document["normalized_text"],
        "sentences": document["sentences"],
        "entities": [],
        "schema_version": PACKAGE_VERSION,
    }


def build_tasks(selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for item in selected:
        question = item["question"]
        answer = item["answer"]
        tasks.append(
            {
                "task_id": f"gold-v1-{item['sample_sequence']:03d}",
                "parent_record_id": item["parent_record_id"],
                "sample_sequence": item["sample_sequence"],
                "strata": item["strata"],
                "title": question["title"],
                "url": question["url"],
                "question": task_document(question),
                "answer": task_document(answer),
                "package_version": PACKAGE_VERSION,
                "guideline_version": GUIDELINE_VERSION,
            }
        )
    return tasks


def build_annotation_template(
    tasks: list[dict[str, Any]], annotator_id: str
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in tasks:
        rows.append(
            {
                "task_id": task["task_id"],
                "parent_record_id": task["parent_record_id"],
                "strata": task["strata"],
                "question": extraction_template(task["question"]),
                "answer": extraction_template(task["answer"]),
                "annotation_meta": {
                    "annotator_id": annotator_id,
                    "status": "pending",
                    "guideline_version": GUIDELINE_VERSION,
                    "annotated_at": None,
                    "notes": "",
                },
            }
        )
    return rows


def write_template_safely(
    path: Path,
    rows: list[dict[str, Any]],
    overwrite: bool,
) -> str:
    if path.exists() and not overwrite:
        return "preserved_existing"
    write_jsonl(path, rows)
    return "created" if not overwrite else "overwritten"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare the Milestone A Checkpoint 3 annotation package."
    )
    parser.add_argument(
        "--input-file",
        default="Riset/Tahap_2/checkpoint_01/stage2_checkpoint_01_input.jsonl",
    )
    parser.add_argument(
        "--tasks-file",
        default="Riset/Tahap_2/checkpoint_03/stage2_annotation_tasks.jsonl",
    )
    parser.add_argument(
        "--annotator-a-file",
        default="Riset/Tahap_2/checkpoint_03/stage2_annotator_a.jsonl",
    )
    parser.add_argument(
        "--annotator-b-file",
        default="Riset/Tahap_2/checkpoint_03/stage2_annotator_b.jsonl",
    )
    parser.add_argument(
        "--manifest-file",
        default="Riset/Tahap_2/checkpoint_03/stage2_sampling_manifest.json",
    )
    parser.add_argument("--sample-size", type=int, default=40)
    parser.add_argument("--seed", default="stage2-gold-v1")
    parser.add_argument("--overwrite-templates", action="store_true")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    tasks_path = Path(args.tasks_file)
    annotator_a_path = Path(args.annotator_a_file)
    annotator_b_path = Path(args.annotator_b_file)
    manifest_path = Path(args.manifest_file)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    pairs, validation_failures = validate_and_pair(input_path)
    if validation_failures:
        raise ValueError(
            f"Checkpoint 1 input has {len(validation_failures)} validation failures"
        )

    selected, population_counts, selected_counts = stratified_sample(
        pairs, sample_size=args.sample_size, seed=args.seed
    )
    tasks = build_tasks(selected)
    write_jsonl(tasks_path, tasks)
    template_status = {
        "annotator_a": write_template_safely(
            annotator_a_path,
            build_annotation_template(tasks, "ANNOTATOR_A"),
            overwrite=args.overwrite_templates,
        ),
        "annotator_b": write_template_safely(
            annotator_b_path,
            build_annotation_template(tasks, "ANNOTATOR_B"),
            overwrite=args.overwrite_templates,
        ),
    }

    manifest = {
        "checkpoint": CHECKPOINT_NAME,
        "package_version": PACKAGE_VERSION,
        "guideline_version": GUIDELINE_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ready_for_annotation",
        "seed": args.seed,
        "sample_size": args.sample_size,
        "input": {
            "path": str(input_path),
            "sha256": sha256_bytes(input_path.read_bytes()),
            "document_count": len(pairs) * 2,
            "pair_count": len(pairs),
        },
        "outputs": {
            "tasks": str(tasks_path),
            "annotator_a": str(annotator_a_path),
            "annotator_b": str(annotator_b_path),
        },
        "template_status": template_status,
        "population_strata": dict(sorted(population_counts.items())),
        "selected_strata": dict(sorted(selected_counts.items())),
        "selected_parent_record_ids": [
            item["parent_record_id"] for item in selected
        ],
        "exit_criteria": {
            "checkpoint_01_input_valid": not validation_failures,
            "sample_size_matches_request": len(selected) == args.sample_size,
            "all_selected_pairs_complete": all(
                set((item["question"]["source_field"], item["answer"]["source_field"]))
                == {"question", "answer"}
                for item in selected
            ),
            "task_ids_unique": len({task["task_id"] for task in tasks}) == len(tasks),
            "parent_record_ids_unique": len(
                {task["parent_record_id"] for task in tasks}
            )
            == len(tasks),
            "stratification_available": all(task["strata"] for task in tasks),
            "independent_templates_available": annotator_a_path.exists()
            and annotator_b_path.exists(),
        },
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    summary = {
        "status": manifest["status"],
        "population_pairs": len(pairs),
        "selected_pairs": len(selected),
        "selected_documents": len(selected) * 2,
        "selected_strata": manifest["selected_strata"],
        "template_status": template_status,
        "tasks_file": str(tasks_path),
        "manifest_file": str(manifest_path),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if all(manifest["exit_criteria"].values()) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        print(f"Checkpoint 3 preparation failed: {error}", file=sys.stderr)
        raise SystemExit(2)
