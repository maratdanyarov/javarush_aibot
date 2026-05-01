from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import PostStatus, SourceType


# Keyword Schemas
class KeywordBase(BaseModel):
    word: str
    enabled: bool = True


class KeywordCreate(KeywordBase):
    pass


class KeywordUpdate(BaseModel):
    word: str | None = None
    enabled: bool | None = None


class KeywordRead(KeywordBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Source Schemas
class SourceBase(BaseModel):
    name: str
    type: SourceType = SourceType.site
    url: str
    enabled: bool = True


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: str | None = None
    type: SourceType | None = None
    url: str | None = None
    enabled: bool | None = None


class SourceRead(SourceBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


# NewsItems Schemas
class NewsItemBase(BaseModel):
    title: str
    url: str | None = None
    summary: str
    raw_text: str | None = None
    source: str
    source_id: str | None = None
    published_at: datetime


class NewsItemCreate(NewsItemBase):
    pass


class NewsItemUpdate(BaseModel):
    title: str | None = None
    url: str | None = None
    summary: str | None = None

    raw_text: str | None = None
    source: str | None = None
    source_id: str | None = None
    published_at: datetime | None = None


class NewsItemRead(NewsItemBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Post Schemas
class PostBase(BaseModel):
    news_id: str
    generated_text: str
    status: PostStatus = PostStatus.new
    published_at: datetime | None = None
    error_message: str | None = None


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    news_id: str | None = None
    generated_text: str | None = None
    status: PostStatus | None = None
    published_at: datetime | None = None
    error_message: str | None = None


class PostRead(PostBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
