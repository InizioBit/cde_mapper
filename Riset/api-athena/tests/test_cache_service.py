from __future__ import annotations

from datetime import timedelta
import unittest

from app.services.cache_service import (
    build_cache_key,
    expires_at,
    is_cache_valid,
    normalize_filters,
    utc_now,
)


class DummyCacheRow:
    def __init__(self, expires_at_value):
        self.expires_at = expires_at_value


class CacheServiceTest(unittest.TestCase):
    def test_build_cache_key_normalizes_query_and_domain(self) -> None:
        first = build_cache_key(
            " Diabetes ",
            domain=" Condition ",
            page=1,
            filters={"vocabulary": "SNOMED", "concept_class": None},
        )
        second = build_cache_key(
            "diabetes",
            domain="condition",
            page=1,
            filters={"vocabulary": "SNOMED"},
        )

        self.assertEqual(first, second)

    def test_build_cache_key_changes_when_page_changes(self) -> None:
        first = build_cache_key("diabetes", domain="Condition", page=1)
        second = build_cache_key("diabetes", domain="Condition", page=2)

        self.assertNotEqual(first, second)

    def test_normalize_filters_removes_none_values_and_sorts(self) -> None:
        filters = normalize_filters(
            {
                "vocabulary": "SNOMED",
                "standard_concept": None,
                "concept_class": "Disorder",
            }
        )

        self.assertEqual(
            filters,
            {
                "concept_class": "Disorder",
                "vocabulary": "SNOMED",
            },
        )

    def test_expires_at_is_in_future(self) -> None:
        self.assertGreater(expires_at(days=1), utc_now())

    def test_is_cache_valid_detects_valid_and_expired_rows(self) -> None:
        valid_row = DummyCacheRow(utc_now() + timedelta(days=1))
        expired_row = DummyCacheRow(utc_now() - timedelta(days=1))

        self.assertTrue(is_cache_valid(valid_row))
        self.assertFalse(is_cache_valid(expired_row))
        self.assertFalse(is_cache_valid(None))
