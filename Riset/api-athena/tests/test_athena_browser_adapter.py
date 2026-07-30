from __future__ import annotations

import unittest

from app.services.athena_browser_adapter import (
    AthenaBrowserAdapter,
    AthenaSearchParams,
)


class AthenaBrowserAdapterTest(unittest.TestCase):
    def test_build_search_url_matches_athena_route(self) -> None:
        adapter = AthenaBrowserAdapter()
        url = adapter.build_search_url(
            AthenaSearchParams(query="heart rate", domain="Condition", page=1)
        )

        self.assertEqual(
            url,
            "https://athena.ohdsi.org/search-terms/terms?"
            "query=heart+rate&boosts=&page=1&domain=Condition",
        )

    def test_build_download_csv_url_matches_athena_route(self) -> None:
        adapter = AthenaBrowserAdapter()
        url = adapter.build_download_csv_url(
            AthenaSearchParams(query="diabetes", domain="Condition", page=2)
        )

        self.assertEqual(
            url,
            "https://athena.ohdsi.org/api/v1/concepts/download/csv?"
            "query=diabetes&boosts=&page=2&domain=Condition",
        )

    def test_build_download_csv_url_supports_page_size_and_list_filters(self) -> None:
        adapter = AthenaBrowserAdapter()
        url = adapter.build_download_csv_url(
            AthenaSearchParams(
                query="diabetes",
                domain=["Condition"],
                page=1,
                page_size=15,
                vocabulary=["SNOMED", "LOINC"],
                standard_concept=["Standard", "Classification"],
                invalid_reason="Valid",
            )
        )

        self.assertIn("pageSize=15", url)
        self.assertIn("domain=Condition", url)
        self.assertIn("vocabulary=SNOMED", url)
        self.assertIn("vocabulary=LOINC", url)
        self.assertIn("standardConcept=Standard", url)
        self.assertIn("standardConcept=Classification", url)
        self.assertIn("invalidReason=Valid", url)

    def test_extract_results_from_tab_separated_csv(self) -> None:
        adapter = AthenaBrowserAdapter()
        body = "\n".join(
            [
                "Id\tCode\tName\tStandard Class\tDomain\tVocab\tValidity\tConcept",
                "201826\t44054006\tType 2 diabetes mellitus\tDisorder\t"
                "Condition\tSNOMED\tValid\tStandard",
            ]
        )

        results = adapter._extract_results_from_csv_text(body)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["concept_id"], 201826)
        self.assertEqual(results[0]["concept_code"], "44054006")
        self.assertEqual(results[0]["concept_name"], "Type 2 diabetes mellitus")
        self.assertEqual(results[0]["domain_id"], "Condition")
        self.assertEqual(results[0]["vocabulary_id"], "SNOMED")
        self.assertEqual(results[0]["concept_class_id"], "Disorder")
        self.assertEqual(results[0]["standard_concept"], "Standard")
        self.assertEqual(results[0]["invalid_reason"], "Valid")

    def test_record_from_dom_row_uses_athena_column_order(self) -> None:
        adapter = AthenaBrowserAdapter()
        record = adapter._record_from_row_values(
            [
                "201826",
                "44054006",
                "Type 2 diabetes mellitus",
                "Disorder",
                "Condition",
                "SNOMED",
                "Valid",
                "Standard",
            ]
        )

        self.assertEqual(record["concept_id"], 201826)
        self.assertEqual(record["concept_code"], "44054006")
        self.assertEqual(record["concept_name"], "Type 2 diabetes mellitus")
        self.assertEqual(record["domain_id"], "Condition")

    def test_apply_pagination_slices_csv_results(self) -> None:
        adapter = AthenaBrowserAdapter()
        results = [
            {"concept_id": 1},
            {"concept_id": 2},
            {"concept_id": 3},
        ]

        page = adapter._apply_pagination(
            results,
            AthenaSearchParams(query="x", page=2, page_size=1),
        )

        self.assertEqual(page, [{"concept_id": 2}])
