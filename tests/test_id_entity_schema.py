from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from pydantic import ValidationError

from rag.id_entity_schema import (
    ClinicalExtractionDocument,
    Stage2InputDocument,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class Stage2EntitySchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        checkpoint_01 = (
            REPO_ROOT
            / "Riset/Tahap_2/checkpoint_01/stage2_checkpoint_01_input.jsonl"
        )
        cls.input_payload = json.loads(
            checkpoint_01.read_text(encoding="utf-8").splitlines()[0]
        )
        examples_path = (
            REPO_ROOT
            / "Riset/Tahap_2/checkpoint_02/stage2_schema_examples.jsonl"
        )
        cls.example_payloads = []
        for line in examples_path.read_text(encoding="utf-8").splitlines():
            raw = json.loads(line)
            cls.example_payloads.append(
                {key: value for key, value in raw.items() if key != "example_id"}
            )

    def test_checkpoint_01_document_is_valid(self):
        document = Stage2InputDocument.model_validate(self.input_payload)
        self.assertEqual(document.source_field, "question")
        self.assertEqual(document.speaker, "patient")

    def test_all_positive_examples_are_valid(self):
        for payload in self.example_payloads:
            ClinicalExtractionDocument.model_validate(payload)

    def test_mention_offset_mismatch_is_rejected(self):
        payload = copy.deepcopy(self.example_payloads[0])
        payload["entities"][0]["start_char"] = 0
        with self.assertRaisesRegex(ValidationError, "mention-offset mismatch"):
            ClinicalExtractionDocument.model_validate(payload)

    def test_duplicate_entity_id_is_rejected(self):
        payload = copy.deepcopy(self.example_payloads[2])
        payload["entities"][1]["entity_id"] = payload["entities"][0]["entity_id"]
        with self.assertRaisesRegex(ValidationError, "duplicate entity_id"):
            ClinicalExtractionDocument.model_validate(payload)

    def test_question_doctor_speaker_is_rejected(self):
        payload = copy.deepcopy(self.example_payloads[0])
        payload["entities"][0]["speaker"] = "doctor"
        with self.assertRaisesRegex(ValidationError, "speaker must be 'patient'"):
            ClinicalExtractionDocument.model_validate(payload)


if __name__ == "__main__":
    unittest.main()
