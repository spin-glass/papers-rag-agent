from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any, List, Optional

class HealthResponse(BaseModel):
    ok: bool = True
    rag_ready: bool
    size: int

class InitIndexRequest(BaseModel):
    force: bool = Field(default=True)

class InitIndexResponse(BaseModel):
    ok: bool
    size: int

class ArxivSearchRequest(BaseModel):
    query: str
    max_results: int = 10

class Paper(BaseModel):
    id: str
    title: str
    url: Optional[str] = None
    summary: Optional[str] = None
    authors: Optional[List[str]] = None

class ArxivSearchResponse(BaseModel):
    ok: bool
    count: int
    items: List[Paper]

class AskRequest(BaseModel):
    query: str

class AskResponse(BaseModel):
    ok: bool
    answer: str
    citations: Optional[List[Any]] = None
