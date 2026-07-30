from __future__ import annotations

import logging
from time import perf_counter
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.athena_browser_adapter import (
    AthenaAdapterError,
    AthenaBrowserAdapter,
    AthenaRenderError,
    AthenaSearchParams,
    AthenaTimeoutError,
)
from app.services.cache_service import (
    build_cache_key,
    get_search_cache,
    normalize_filters,
    save_search_cache,
)


logger = logging.getLogger(__name__)
StringOrList = str | list[str]


class AthenaSearchServiceError(RuntimeError):
    pass


class AthenaSearchValidationError(AthenaSearchServiceError):
    pass


class AthenaSearchTimeoutError(AthenaSearchServiceError):
    pass


class AthenaSearchParsingError(AthenaSearchServiceError):
    pass


class AthenaSearchUpstreamError(AthenaSearchServiceError):
    pass


class AthenaSearchService:
    def __init__(
        self,
        session: AsyncSession,
        adapter: AthenaBrowserAdapter | None = None,
    ) -> None:
        self.session = session
        self.adapter = adapter or AthenaBrowserAdapter()

    async def search(
        self,
        *,
        query: str,
        domain: StringOrList | None = None,
        page: int = 1,
        page_size: int | None = None,
        standard_concept: StringOrList | None = None,
        vocabulary: StringOrList | None = None,
        concept_class: StringOrList | None = None,
        invalid_reason: StringOrList | None = None,
        response_format: str = "local",
        refresh: bool = False,
    ) -> dict[str, Any]:
        clean_query = query.strip()
        if not clean_query:
            logger.warning("search_validation_error reason=query_empty")
            raise AthenaSearchValidationError("Query must not be empty.")

        clean_domain = self._clean_optional(domain)
        clean_response_format = response_format.strip().lower()
        if clean_response_format not in {"local", "athena"}:
            raise AthenaSearchValidationError(
                "format must be either 'local' or 'athena'."
            )
        filters = normalize_filters(
            {
                "standard_concept": self._clean_optional(standard_concept),
                "vocabulary": self._clean_optional(vocabulary),
                "concept_class": self._clean_optional(concept_class),
                "invalid_reason": self._clean_optional(invalid_reason),
                "page_size": page_size,
                "format": clean_response_format,
            }
        )
        cache_key = build_cache_key(
            clean_query,
            domain=clean_domain,
            page=page,
            filters=filters,
        )

        cached_response: dict[str, Any] | None = None
        if not refresh:
            cached_response, is_valid = await get_search_cache(self.session, cache_key)
            if cached_response and is_valid:
                logger.info(
                    "cache_hit query=%r domain=%r page=%s cache_key=%s result_count=%s",
                    clean_query,
                    clean_domain,
                    page,
                    cache_key,
                    cached_response.get("result_count"),
                )
                return self._with_cache_metadata(
                    cached_response,
                    hit=True,
                    stale=False,
                    key=cache_key,
                )
        else:
            cached_response, _ = await get_search_cache(self.session, cache_key)

        logger.info(
            "cache_miss query=%r domain=%r page=%s refresh=%s cache_key=%s",
            clean_query,
            clean_domain,
            page,
            refresh,
            cache_key,
        )

        params = AthenaSearchParams(
            query=clean_query,
            domain=clean_domain,
            page=page,
            page_size=page_size,
            standard_concept=filters.get("standard_concept"),
            vocabulary=filters.get("vocabulary"),
            concept_class=filters.get("concept_class"),
            invalid_reason=filters.get("invalid_reason"),
        )

        try:
            started_at = perf_counter()
            response = await self.adapter.search(params)
        except AthenaTimeoutError as exc:
            if cached_response:
                logger.warning(
                    "athena_timeout_stale_cache query=%r domain=%r page=%s cache_key=%s error=%r",
                    clean_query,
                    clean_domain,
                    page,
                    cache_key,
                    str(exc),
                )
                return self._with_cache_metadata(
                    cached_response,
                    hit=True,
                    stale=True,
                    key=cache_key,
                    upstream_error=str(exc),
                )
            logger.error(
                "athena_timeout query=%r domain=%r page=%s error=%r",
                clean_query,
                clean_domain,
                page,
                str(exc),
            )
            raise AthenaSearchTimeoutError(str(exc)) from exc
        except AthenaRenderError as exc:
            if cached_response:
                logger.warning(
                    "athena_parse_error_stale_cache query=%r domain=%r page=%s cache_key=%s error=%r",
                    clean_query,
                    clean_domain,
                    page,
                    cache_key,
                    str(exc),
                )
                return self._with_cache_metadata(
                    cached_response,
                    hit=True,
                    stale=True,
                    key=cache_key,
                    upstream_error=str(exc),
                )
            logger.error(
                "athena_parse_error query=%r domain=%r page=%s error=%r",
                clean_query,
                clean_domain,
                page,
                str(exc),
            )
            raise AthenaSearchParsingError(str(exc)) from exc
        except AthenaAdapterError as exc:
            if cached_response:
                logger.warning(
                    "athena_upstream_error_stale_cache query=%r domain=%r page=%s cache_key=%s error=%r",
                    clean_query,
                    clean_domain,
                    page,
                    cache_key,
                    str(exc),
                )
                return self._with_cache_metadata(
                    cached_response,
                    hit=True,
                    stale=True,
                    key=cache_key,
                    upstream_error=str(exc),
                )
            logger.error(
                "athena_upstream_error query=%r domain=%r page=%s error=%r",
                clean_query,
                clean_domain,
                page,
                str(exc),
            )
            raise AthenaSearchUpstreamError(str(exc)) from exc

        duration_ms = int((perf_counter() - started_at) * 1000)
        logger.info(
            "athena_search_success query=%r domain=%r page=%s source=%s result_count=%s duration_ms=%s",
            clean_query,
            clean_domain,
            page,
            response.get("source"),
            response.get("result_count"),
            duration_ms,
        )

        response = self._with_cache_metadata(
            self._format_response(response, clean_response_format, page_size),
            hit=False,
            stale=False,
            key=cache_key,
        )
        await save_search_cache(
            self.session,
            cache_key=cache_key,
            query=clean_query,
            domain=self._stringify_optional(clean_domain),
            page=page,
            filters=filters,
            response=response,
        )
        logger.info(
            "cache_save query=%r domain=%r page=%s cache_key=%s result_count=%s",
            clean_query,
            clean_domain,
            page,
            cache_key,
            response.get("result_count"),
        )
        return response

    def _with_cache_metadata(
        self,
        response: dict[str, Any],
        *,
        hit: bool,
        stale: bool,
        key: str,
        upstream_error: str | None = None,
    ) -> dict[str, Any]:
        response = dict(response)
        response["cached"] = hit
        response["stale"] = stale
        response["cache"] = {
            "hit": hit,
            "stale": stale,
            "key": key,
        }
        if upstream_error:
            response["cache"]["upstream_error"] = upstream_error
        return response

    def _format_response(
        self,
        response: dict[str, Any],
        response_format: str,
        page_size: int | None,
    ) -> dict[str, Any]:
        if response_format != "athena":
            return response

        content = [
            self._to_athena_compatible_record(item)
            for item in response.get("results", [])
        ]
        return {
            "content": content,
            "query": response.get("query"),
            "domain": response.get("domain"),
            "page": response.get("page", 1),
            "pageSize": page_size,
            "source": response.get("source"),
            "result_count": len(content),
            "total_result_count": response.get("total_result_count", len(content)),
            "results": response.get("results", []),
        }

    def _to_athena_compatible_record(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item.get("concept_id"),
            "code": item.get("concept_code"),
            "name": item.get("concept_name"),
            "domain": item.get("domain_id"),
            "vocabulary": item.get("vocabulary_id"),
            "standardConcept": item.get("standard_concept"),
            "className": item.get("concept_class_id"),
            "invalidReason": item.get("invalid_reason"),
        }

    def _clean_optional(self, value: StringOrList | None) -> StringOrList | None:
        if value is None:
            return None
        if isinstance(value, list):
            cleaned_values = [item.strip() for item in value if item and item.strip()]
            return cleaned_values or None
        cleaned = value.strip()
        return cleaned or None

    def _stringify_optional(self, value: StringOrList | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, list):
            return "|".join(value)
        return value
