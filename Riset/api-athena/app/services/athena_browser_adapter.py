from __future__ import annotations

import asyncio
import csv
import gzip
import io
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from playwright.async_api import Browser, Page, TimeoutError, async_playwright

from app.config import get_settings


logger = logging.getLogger(__name__)
StringOrList = str | list[str]


class AthenaAdapterError(RuntimeError):
    pass


class AthenaTimeoutError(AthenaAdapterError):
    pass


class AthenaRenderError(AthenaAdapterError):
    pass


@dataclass(frozen=True)
class AthenaSearchParams:
    query: str
    domain: StringOrList | None = None
    page: int = 1
    page_size: int | None = None
    standard_concept: StringOrList | None = None
    vocabulary: StringOrList | None = None
    concept_class: StringOrList | None = None
    invalid_reason: StringOrList | None = None

    def as_filters(self) -> dict[str, StringOrList]:
        filters = {
            "standardConcept": self.standard_concept,
            "vocabulary": self.vocabulary,
            "conceptClass": self.concept_class,
            "invalidReason": self.invalid_reason,
        }
        return {key: value for key, value in filters.items() if value}


class AthenaBrowserAdapter:
    def __init__(self) -> None:
        self.settings = get_settings()

    def build_search_url(self, params: AthenaSearchParams) -> str:
        query_params: dict[str, Any] = {
            "query": params.query,
            "boosts": "",
            "page": params.page,
        }
        if params.page_size:
            query_params["pageSize"] = params.page_size
        if params.domain:
            query_params["domain"] = params.domain
        query_params.update(params.as_filters())

        return (
            f"{self.settings.athena_base_url}/search-terms/terms?"
            f"{urlencode(query_params, doseq=True)}"
        )

    def build_download_csv_url(self, params: AthenaSearchParams) -> str:
        query_params: dict[str, Any] = {
            "query": params.query,
            "boosts": "",
            "page": params.page,
        }
        if params.page_size:
            query_params["pageSize"] = params.page_size
        if params.domain:
            query_params["domain"] = params.domain
        query_params.update(params.as_filters())

        return (
            f"{self.settings.athena_base_url}/api/v1/concepts/download/csv?"
            f"{urlencode(query_params, doseq=True)}"
        )

    def build_concept_url(self, concept_id: int) -> str:
        return f"{self.settings.athena_base_url}/search-terms/terms/{concept_id}"

    async def search(self, params: AthenaSearchParams) -> dict[str, Any]:
        url = self.build_search_url(params)
        csv_results = await self._extract_results_from_csv_http(params)
        if csv_results is not None:
            total_result_count = len(csv_results)
            csv_results = self._apply_pagination(csv_results, params)
            logger.info(
                "athena_direct_csv_results result_count=%s query=%r domain=%r page=%s",
                len(csv_results),
                params.query,
                params.domain,
                params.page,
            )
            return {
                "query": params.query,
                "domain": params.domain,
                "page": params.page,
                "source": "athena_csv_http",
                "result_count": len(csv_results),
                "total_result_count": total_result_count,
                "results": csv_results,
            }

        raise AthenaAdapterError(
            "Athena direct CSV download failed; browser fallback is disabled for search."
        )

        logger.info(
            "athena_browser_open url=%s query=%r domain=%r page=%s",
            url,
            params.query,
            params.domain,
            params.page,
        )
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(
                    headless=self.settings.playwright_headless
                )
                try:
                    page = await browser.new_page(
                        viewport={"width": 1366, "height": 900},
                        user_agent=(
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/149.0 Safari/537.36"
                        ),
                    )
                    await self._block_nonessential_resources(page)
                    captured_payloads: list[Any] = []
                    page.on(
                        "response",
                        lambda response: asyncio.create_task(
                            self._capture_json_response(response, captured_payloads)
                        ),
                    )

                    await self._goto(page, url)
                    await self._ensure_app_loaded(page)
                    await self._accept_license_if_present(page)
                    await self._wait_for_search_render(page)

                    results = self._extract_results_from_payloads(captured_payloads)
                    source = "athena_network"
                    if not results:
                        results = await self._extract_results_from_dom(page)
                        source = "athena_dom"

                    if not results:
                        results = await self._extract_results_from_csv_download(page, params)
                        source = "athena_csv"

                    if not results:
                        if await self._has_no_data(page):
                            return {
                                "query": params.query,
                                "domain": params.domain,
                                "page": params.page,
                                "source": source,
                                "result_count": 0,
                                "results": [],
                            }
                        debug_path = await self._save_debug_html(page, "search")
                        logger.error(
                            "athena_parse_failed url=%s debug_html=%s",
                            url,
                            debug_path,
                        )
                        raise AthenaRenderError(
                            f"Athena search rendered no parseable results. "
                            f"Debug HTML: {debug_path}"
                        )

                    logger.info(
                        "athena_browser_results source=%s result_count=%s url=%s",
                        source,
                        len(results),
                        url,
                    )
                    total_result_count = len(results)
                    results = self._apply_pagination(results, params)
                    return {
                        "query": params.query,
                        "domain": params.domain,
                        "page": params.page,
                        "source": source,
                        "result_count": len(results),
                        "total_result_count": total_result_count,
                        "results": results,
                    }
                finally:
                    await browser.close()
        except AthenaAdapterError:
            raise
        except Exception as exc:
            logger.exception("athena_browser_error url=%s", url)
            raise AthenaAdapterError(f"Athena browser adapter failed: {exc}") from exc

    async def get_concept_detail(self, concept_id: int) -> dict[str, Any]:
        url = self.build_concept_url(concept_id)
        logger.info("athena_concept_open concept_id=%s url=%s", concept_id, url)
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=self.settings.playwright_headless
            )
            try:
                page = await browser.new_page(viewport={"width": 1366, "height": 900})
                await self._block_nonessential_resources(page)
                await self._goto(page, url)
                await self._ensure_app_loaded(page)
                await self._accept_license_if_present(page)
                await page.wait_for_timeout(3000)
                body_text = await page.locator("body").inner_text(timeout=5000)
                if not body_text.strip():
                    debug_path = await self._save_debug_html(page, "concept")
                    logger.error(
                        "athena_concept_parse_failed concept_id=%s debug_html=%s",
                        concept_id,
                        debug_path,
                    )
                    raise AthenaRenderError(
                        f"Athena concept detail rendered no text. Debug HTML: {debug_path}"
                    )
                return {
                    "concept_id": concept_id,
                    "source": "athena_dom",
                    "text": body_text,
                }
            finally:
                await browser.close()

    async def _block_nonessential_resources(self, page: Page) -> None:
        async def route_handler(route):
            url = route.request.url
            resource_type = route.request.resource_type
            if (
                "googletagmanager" in url
                or "google-analytics" in url
                or resource_type in {"image", "media", "font"}
            ):
                await route.abort()
                return
            await route.continue_()

        await page.route("**/*", route_handler)

    async def _goto(self, page: Page, url: str) -> None:
        try:
            await page.goto(
                url,
                wait_until="commit",
                timeout=self.settings.athena_timeout_seconds * 1000,
            )
        except TimeoutError as exc:
            raise AthenaTimeoutError(f"Timed out opening Athena URL: {url}") from exc

    async def _ensure_app_loaded(self, page: Page) -> None:
        await page.wait_for_timeout(1000)
        app_html = await page.locator("#app").inner_html(timeout=3000)
        if app_html.strip():
            return

        script_src = await page.locator("script[src*='app.']").first.get_attribute("src")
        if not script_src:
            return

        if script_src.startswith("/"):
            script_src = f"{self.settings.athena_base_url}{script_src}"

        try:
            await page.add_script_tag(url=script_src)
            await page.wait_for_timeout(5000)
        except Exception:
            return

    async def _accept_license_if_present(self, page: Page) -> None:
        button = page.locator("button", has_text="Accept").first
        try:
            if await button.count():
                await button.click(timeout=3000)
                await page.wait_for_timeout(3000)
        except Exception:
            return

    async def _wait_for_search_render(self, page: Page) -> None:
        deadline_ms = self.settings.athena_timeout_seconds * 1000
        selectors = [
            "table tbody tr",
            "[role='row']",
            "a[href*='/search-terms/terms/']",
            "text=Concept",
        ]

        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=deadline_ms // len(selectors))
                return
            except TimeoutError:
                continue

        await page.wait_for_timeout(3000)

    async def _capture_json_response(self, response, captured_payloads: list[Any]) -> None:
        url = response.url
        if "/api/" not in url and "/terms" not in url:
            return
        content_type = response.headers.get("content-type", "")
        if "json" not in content_type:
            return
        try:
            captured_payloads.append(await response.json())
        except Exception:
            return

    def _extract_results_from_payloads(self, payloads: list[Any]) -> list[dict[str, Any]]:
        for payload in payloads:
            candidates = self._find_candidate_records(payload)
            normalized = [self._normalize_record(record) for record in candidates]
            normalized = [record for record in normalized if record.get("concept_id")]
            if normalized:
                return normalized
        return []

    def _find_candidate_records(self, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]

        if not isinstance(payload, dict):
            return []

        for key in ("data", "items", "results", "content", "rows"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            if isinstance(value, dict):
                nested = self._find_candidate_records(value)
                if nested:
                    return nested

        return []

    async def _extract_results_from_dom(self, page: Page) -> list[dict[str, Any]]:
        table_results = await self._extract_table_rows(page)
        if table_results:
            return table_results
        return await self._extract_links(page)

    async def _extract_results_from_csv_download(
        self, page: Page, params: AthenaSearchParams
    ) -> list[dict[str, Any]]:
        url = self.build_download_csv_url(params)
        logger.info("athena_csv_download url=%s", url)
        try:
            response = await page.request.get(
                url,
                headers={"Accept": "text/csv,*/*"},
                timeout=self.settings.athena_timeout_seconds * 1000,
            )
        except Exception:
            logger.exception("athena_csv_download_error url=%s", url)
            return []

        if not response.ok:
            logger.warning(
                "athena_csv_download_bad_status url=%s status=%s",
                url,
                response.status,
            )
            return []

        try:
            body = await response.text()
        except Exception:
            logger.exception("athena_csv_read_error url=%s", url)
            return []

        results = self._extract_results_from_csv_text(body)
        logger.info(
            "athena_csv_parsed url=%s result_count=%s",
            url,
            len(results),
        )
        return results

    async def _extract_results_from_csv_http(
        self, params: AthenaSearchParams
    ) -> list[dict[str, Any]] | None:
        url = self.build_download_csv_url(params)
        logger.info("athena_direct_csv_download url=%s", url)
        try:
            body = await asyncio.to_thread(self._download_csv_text, url)
        except HTTPError as exc:
            if exc.code == 400:
                logger.info(
                    "athena_direct_csv_bad_request_as_empty url=%s status=%s",
                    url,
                    exc.code,
                )
                return []
            logger.warning(
                "athena_direct_csv_download_error url=%s error=%r",
                url,
                str(exc),
            )
            return None
        except Exception as exc:
            logger.warning(
                "athena_direct_csv_download_error url=%s error=%r",
                url,
                str(exc),
            )
            return None

        results = self._extract_results_from_csv_text(body)
        logger.info(
            "athena_direct_csv_parsed url=%s result_count=%s",
            url,
            len(results),
        )
        return results

    def _download_csv_text(self, url: str) -> str:
        request = Request(
            url,
            headers={
                "Accept": "text/csv,*/*",
                "Accept-Encoding": "gzip",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/149.0 Safari/537.36"
                ),
            },
        )
        with urlopen(request, timeout=self.settings.athena_timeout_seconds) as response:
            body = response.read()
            if response.headers.get("Content-Encoding", "").lower() == "gzip":
                body = gzip.decompress(body)
            charset = response.headers.get_content_charset() or "utf-8"
            return body.decode(charset, errors="replace")

    def _extract_results_from_csv_text(self, body: str) -> list[dict[str, Any]]:
        if not body.strip():
            return []

        sample = body[:2048]
        delimiter = "\t" if "\t" in sample else ","
        reader = csv.DictReader(io.StringIO(body), delimiter=delimiter)
        results = [self._record_from_csv_row(row) for row in reader]
        return [record for record in results if record.get("concept_id")]

    def _apply_pagination(
        self,
        results: list[dict[str, Any]],
        params: AthenaSearchParams,
    ) -> list[dict[str, Any]]:
        if not params.page_size:
            return results
        start = (params.page - 1) * params.page_size
        end = start + params.page_size
        return results[start:end]

    async def _has_no_data(self, page: Page) -> bool:
        try:
            text = await page.locator("table tbody").inner_text(timeout=3000)
        except Exception:
            return False
        return "no data available" in text.lower()

    async def _extract_table_rows(self, page: Page) -> list[dict[str, Any]]:
        rows = page.locator("table tbody tr")
        count = await rows.count()
        results: list[dict[str, Any]] = []

        for index in range(count):
            cells = rows.nth(index).locator("td")
            cell_count = await cells.count()
            values = [
                (await cells.nth(cell_index).inner_text()).strip()
                for cell_index in range(cell_count)
            ]
            record = self._record_from_row_values(values)
            if record.get("concept_id"):
                results.append(record)

        return results

    async def _extract_links(self, page: Page) -> list[dict[str, Any]]:
        links = page.locator("a[href*='/search-terms/terms/']")
        count = await links.count()
        results: list[dict[str, Any]] = []
        seen: set[int] = set()

        for index in range(count):
            link = links.nth(index)
            href = await link.get_attribute("href")
            text = (await link.inner_text()).strip()
            concept_id = self._concept_id_from_text(href or "")
            if concept_id is None or concept_id in seen:
                continue
            seen.add(concept_id)
            results.append(
                {
                    "concept_id": concept_id,
                    "concept_name": text or None,
                    "domain_id": None,
                    "vocabulary_id": None,
                    "concept_class_id": None,
                    "standard_concept": None,
                    "concept_code": None,
                    "valid_start_date": None,
                    "valid_end_date": None,
                    "invalid_reason": None,
                }
            )

        return results

    def _record_from_row_values(self, values: list[str]) -> dict[str, Any]:
        return {
            "concept_id": self._concept_id_from_text(self._value_at(values, 0) or ""),
            "concept_name": self._value_at(values, 2),
            "domain_id": self._value_at(values, 4),
            "vocabulary_id": self._value_at(values, 5),
            "concept_class_id": self._value_at(values, 3),
            "standard_concept": self._value_at(values, 7),
            "concept_code": self._value_at(values, 1),
            "valid_start_date": None,
            "valid_end_date": None,
            "invalid_reason": self._value_at(values, 6),
        }

    def _record_from_csv_row(self, row: dict[str, Any]) -> dict[str, Any]:
        normalized = {
            self._normalize_key(key): value.strip() if isinstance(value, str) else value
            for key, value in row.items()
            if key
        }

        return {
            "concept_id": self._first_int(
                normalized,
                "id",
                "conceptid",
                "concept_id",
            ),
            "concept_name": self._first_value(normalized, "name", "conceptname"),
            "domain_id": self._first_value(normalized, "domain", "domainid"),
            "vocabulary_id": self._first_value(
                normalized,
                "vocab",
                "vocabulary",
                "vocabularyid",
            ),
            "concept_class_id": self._first_value(
                normalized,
                "standardclass",
                "class",
                "conceptclass",
                "conceptclassid",
            ),
            "standard_concept": self._first_value(
                normalized,
                "concept",
                "standardconcept",
            ),
            "concept_code": self._first_value(normalized, "code", "conceptcode"),
            "valid_start_date": self._first_value(
                normalized,
                "validstartdate",
                "valid_start_date",
            ),
            "valid_end_date": self._first_value(
                normalized,
                "validenddate",
                "valid_end_date",
            ),
            "invalid_reason": self._first_value(
                normalized,
                "validity",
                "invalidreason",
                "invalid_reason",
            ),
        }

    def _normalize_record(self, record: dict[str, Any]) -> dict[str, Any]:
        return {
            "concept_id": self._first_int(record, "conceptId", "concept_id", "id"),
            "concept_name": self._first_value(record, "conceptName", "concept_name", "name"),
            "domain_id": self._first_value(record, "domainId", "domain_id", "domain"),
            "vocabulary_id": self._first_value(
                record, "vocabularyId", "vocabulary_id", "vocabulary"
            ),
            "concept_class_id": self._first_value(
                record, "conceptClassId", "concept_class_id", "conceptClass"
            ),
            "standard_concept": self._first_value(
                record, "standardConcept", "standard_concept"
            ),
            "concept_code": self._first_value(record, "conceptCode", "concept_code"),
            "valid_start_date": self._first_value(
                record, "validStartDate", "valid_start_date"
            ),
            "valid_end_date": self._first_value(record, "validEndDate", "valid_end_date"),
            "invalid_reason": self._first_value(record, "invalidReason", "invalid_reason"),
        }

    def _concept_id_from_text(self, value: str) -> int | None:
        match = re.search(r"(?<!\d)(\d{3,})(?!\d)", value)
        if not match:
            return None
        return int(match.group(1))

    def _first_value(self, record: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            value = record.get(key)
            if value not in (None, ""):
                return value
        return None

    def _first_int(self, record: dict[str, Any], *keys: str) -> int | None:
        value = self._first_value(record, *keys)
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _value_at(self, values: list[str], index: int) -> str | None:
        if index >= len(values):
            return None
        value = values[index].strip()
        return value or None

    def _normalize_key(self, key: str) -> str:
        return re.sub(r"[^a-z0-9]", "", key.lower())

    async def _save_debug_html(self, page: Page, prefix: str) -> Path:
        debug_dir = self.settings.project_root / "debug"
        debug_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = debug_dir / f"{prefix}_{timestamp}.html"
        path.write_text(await page.content(), encoding="utf-8")
        return path
