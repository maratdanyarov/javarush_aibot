"""Pydantic request/response schemas for the AIBot REST API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import PostStatus, SourceType


# Keyword Schemas
class KeywordBase(BaseModel):
    """Shared fields for keyword request and response schemas."""

    word: str
    enabled: bool = True


class KeywordCreate(KeywordBase):
    """Request payload for creating a new keyword."""

    pass


class KeywordUpdate(BaseModel):
    """Request payload for a partial keyword update (all fields optional)."""

    word: str | None = None
    enabled: bool | None = None


class KeywordRead(KeywordBase):
    """Full keyword response including server-assigned ID and timestamp."""

    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Source Schemas
class SourceBase(BaseModel):
    """Shared fields for source request and response schemas."""

    name: str
    type: SourceType = SourceType.site
    url: str
    enabled: bool = True


class SourceCreate(SourceBase):
    """Request payload for creating a new news source."""

    pass


class SourceUpdate(BaseModel):
    """Request payload for a partial source update (all fields optional)."""

    name: str | None = None
    type: SourceType | None = None
    url: str | None = None
    enabled: bool | None = None


class SourceRead(SourceBase):
    """Full source response including server-assigned ID and timestamp."""

    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


# NewsItems Schemas
class NewsItemBase(BaseModel):
    """Shared fields for news item request and response schemas."""

    title: str
    url: str | None = None
    summary: str
    raw_text: str | None = None
    source: str
    source_id: str | None = None
    published_at: datetime


class NewsItemCreate(NewsItemBase):
    """Request payload for creating a new news item."""

    pass


class NewsItemUpdate(BaseModel):
    """Request payload for a partial news item update (all fields optional)."""

    title: str | None = None
    url: str | None = None
    summary: str | None = None

    raw_text: str | None = None
    source: str | None = None
    source_id: str | None = None
    published_at: datetime | None = None


class NewsItemRead(NewsItemBase):
    """Full news item response including server-assigned ID and timestamp."""

    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Post Schemas
class PostBase(BaseModel):
    """Shared fields for post request and response schemas."""

    news_id: str
    generated_text: str
    status: PostStatus = PostStatus.new
    published_at: datetime | None = None
    error_message: str | None = None


class PostCreate(PostBase):
    """Request payload for creating a new post."""

    pass


class PostUpdate(BaseModel):
    """Request payload for a partial post update (all fields optional)."""

    news_id: str | None = None
    generated_text: str | None = None
    status: PostStatus | None = None
    published_at: datetime | None = None
    error_message: str | None = None


class PostRead(PostBase):
    """Full post response including server-assigned ID and timestamp."""

    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class GenerateRequest(BaseModel):
    """Request body for the POST /api/generate endpoint."""

    news_item_id: str
