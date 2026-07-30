from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SearchCache(Base):
    __tablename__ = "search_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cache_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    query: Mapped[str] = mapped_column(String(512), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(128), nullable=True)
    page: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    filters_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    response_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class ConceptCache(Base):
    __tablename__ = "concept_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    concept_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    response_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


Index("ix_search_cache_query_domain_page", SearchCache.query, SearchCache.domain, SearchCache.page)
Index("ix_search_cache_expires_at", SearchCache.expires_at)
Index("ix_concept_cache_expires_at", ConceptCache.expires_at)
