from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.services.cache_service import clear_cache as clear_cache_service
from app.services.cache_service import get_cache_status
from app.services.search_service import (
    AthenaSearchParsingError,
    AthenaSearchService,
    AthenaSearchTimeoutError,
    AthenaSearchUpstreamError,
    AthenaSearchValidationError,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/athena", tags=["athena"])


@router.get("/search")
async def search_terms(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    query: Annotated[str, Query(min_length=1, description="Athena search keyword")],
    domain: Annotated[list[str] | None, Query(description="OMOP domain filter")] = None,
    page: Annotated[int, Query(ge=1, description="Search result page")] = 1,
    page_size: Annotated[
        int | None,
        Query(alias="pageSize", ge=1, description="Search page size"),
    ] = None,
    standard_concept: Annotated[
        str | None, Query(description="OMOP standard concept filter")
    ] = None,
    standard_concept_athena: Annotated[
        list[str] | None,
        Query(alias="standardConcept", description="Athena-style standard concept filter"),
    ] = None,
    vocabulary: Annotated[list[str] | None, Query(description="Vocabulary filter")] = None,
    concept_class: Annotated[
        str | None, Query(description="Concept class filter")
    ] = None,
    concept_class_athena: Annotated[
        list[str] | None,
        Query(alias="conceptClass", description="Athena-style concept class filter"),
    ] = None,
    invalid_reason: Annotated[
        str | None,
        Query(alias="invalidReason", description="Athena-style invalid reason filter"),
    ] = None,
    response_format: Annotated[
        str,
        Query(alias="format", description="Response format: local or athena"),
    ] = "local",
    refresh: Annotated[
        bool, Query(description="Bypass local cache and fetch from Athena")
    ] = False,
) -> dict[str, object]:
    service = AthenaSearchService(session)
    try:
        return await service.search(
            query=query,
            domain=domain,
            page=page,
            page_size=page_size,
            standard_concept=standard_concept_athena or standard_concept,
            vocabulary=vocabulary,
            concept_class=concept_class_athena or concept_class,
            invalid_reason=invalid_reason,
            response_format=response_format,
            refresh=refresh,
        )
    except AthenaSearchValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Invalid Athena search request.",
                "error": str(exc),
            },
        ) from exc
    except AthenaSearchTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={
                "message": "Athena search timed out.",
                "error": str(exc),
            },
        ) from exc
    except AthenaSearchParsingError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": "Athena search response could not be parsed.",
                "error": str(exc),
            },
        ) from exc
    except AthenaSearchUpstreamError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": "Athena search failed.",
                "error": str(exc),
            },
        ) from exc


@router.get("/concepts/{concept_id}")
async def get_concept(concept_id: int) -> dict[str, object]:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "message": "Athena concept detail service is not implemented yet.",
            "next_stage": "Tahap 6",
            "concept_id": concept_id,
        },
    )


@router.get("/cache")
async def cache_status(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, object]:
    status_payload = await get_cache_status(session)
    logger.info(
        "cache_status search_total=%s concept_total=%s",
        status_payload["search_cache"]["total"],
        status_payload["concept_cache"]["total"],
    )
    return status_payload


@router.delete("/cache")
async def clear_cache(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, object]:
    deleted = await clear_cache_service(session)
    logger.warning("cache_clear deleted=%s", deleted)
    return {
        "status": "ok",
        "deleted": deleted,
    }
