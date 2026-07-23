from __future__ import annotations

import unittest

from rag.id_preprocess import IndonesianClinicalNormalizer


class IndonesianClinicalNormalizerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.normalizer = IndonesianClinicalNormalizer.from_resource_dir("data/input")

    def test_question_profile_expands_informal_and_clinical_terms(self):
        result = self.normalizer.normalize(
            "Sy skrg ISK, tp blm minum obat 500mg.",
            audit=True,
            profile="question",
        )
        self.assertEqual(
            result.normalized_text,
            "saya sekarang infeksi saluran kemih, tetapi belum minum obat 500 mg.",
        )
        self.assertGreaterEqual(result.replacements["abbreviation"], 5)

    def test_answer_profile_does_not_expand_informal_layer(self):
        result = self.normalizer.normalize("Alo, sy sudah periksa.", profile="answer")
        self.assertIn("sy sudah periksa", result.normalized_text)
        self.assertEqual(result.content_text, "sy sudah periksa.")
        self.assertEqual(result.boilerplate, ["alo,"])

    def test_context_required_abbreviation_is_preserved_without_context(self):
        result = self.normalizer.normalize(
            "Riwayat TB dalam keluarga.", audit=True, profile="question"
        )
        self.assertIn("tb", result.normalized_text)
        self.assertTrue(result.warnings)

    def test_context_required_measurement_is_expanded(self):
        result = self.normalizer.normalize(
            "BB 70 kg dan TB 165 cm.", profile="clinical"
        )
        self.assertEqual(
            result.normalized_text, "berat badan 70 kg dan tinggi badan 165 cm."
        )

    def test_numbers_units_and_negation_are_preserved(self):
        result = self.normalizer.normalize(
            "Tidak demam, TD 150 / 90 mmhg dan dosis 2,5mg.",
            profile="clinical",
        )
        self.assertIn("tidak demam", result.normalized_text)
        self.assertIn("tekanan darah 150/90 mmHg", result.normalized_text)
        self.assertIn("2,5 mg", result.normalized_text)

    def test_sentence_segmentation_handles_missing_space(self):
        result = self.normalizer.normalize(
            "Saya demam.Dok, apakah berbahaya?Sudah 2 hari.",
            profile="question",
        )
        self.assertEqual(len(result.sentences), 3)

    def test_normalization_is_idempotent(self):
        first = self.normalizer.normalize(
            "Sy dgn DM dan GDP 126mg/dl.", profile="question"
        ).normalized_text
        second = self.normalizer.normalize(first, profile="question").normalized_text
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
