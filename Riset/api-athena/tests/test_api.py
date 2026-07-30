from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app


class ApiTest(unittest.TestCase):
    def test_health_endpoint(self) -> None:
        with TestClient(app) as client:
            response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_cache_status_endpoint(self) -> None:
        with TestClient(app) as client:
            response = client.get("/api/athena/cache")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("search_cache", payload)
        self.assertIn("concept_cache", payload)

    def test_blank_search_query_returns_400(self) -> None:
        with TestClient(app) as client:
            response = client.get("/api/athena/search", params={"query": "   "})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["detail"]["message"],
            "Invalid Athena search request.",
        )

    def test_concept_detail_is_not_implemented_yet(self) -> None:
        with TestClient(app) as client:
            response = client.get("/api/athena/concepts/201826")

        self.assertEqual(response.status_code, 501)
