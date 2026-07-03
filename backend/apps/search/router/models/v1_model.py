# apps/search/router/models/v1_model.py

from typing import Optional
from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):

    query: str = Field(
        ...,
        description="Natural-language search query.",
        min_length=1,
    )

    repo_id: Optional[str] = Field(
        None,
        description=(
            "UUID of a specific repository to search in. "
            "Leave empty to search across all your repositories."
        ),
    )

    top_k: int = Field(
        5,
        description="Maximum number of results to return.",
        ge=1,
        le=50,
    )


class SearchResultItem(BaseModel):

    file: str
    path: str
    filename: str
    language: str
    extension: str
    chunk_index: int
    content: str
    score: float
    repo_id: str
