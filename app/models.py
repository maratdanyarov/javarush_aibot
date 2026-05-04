import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SourceType(StrEnum):
    site = "site"
    telegram = "tg"


class PostStatus(StrEnum):
    new = "new"
    generated = "generated"
    published = "published"
    failed = "failed"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[SourceType] = mapped_column(
        SAEnum(SourceType), default=SourceType.site
    )
    url: Mapped[str] = mapped_column(String(512))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    news_items: Mapped[list["NewsItem"]] = relationship(back_populates="source_rel")


class NewsItem(Base):
    __tablename__ = "news_items"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    title: Mapped[str] = mapped_column(String(512))
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    summary: Mapped[str] = mapped_column(Text)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(255))
    source_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sources.id"), nullable=True
    )
    content_hash: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    source_rel: Mapped["Source | None"] = relationship(back_populates="news_items")
    post: Mapped["Post | None"] = relationship(back_populates="news_item")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    news_id: Mapped[str] = mapped_column(String(36), ForeignKey("news_items.id"))
    generated_text: Mapped[str] = mapped_column(Text)
    status: Mapped[PostStatus] = mapped_column(
        SAEnum(PostStatus), default=PostStatus.new
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    news_item: Mapped["NewsItem"] = relationship(back_populates="post")


class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    word: Mapped[str] = mapped_column(String(255), unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
