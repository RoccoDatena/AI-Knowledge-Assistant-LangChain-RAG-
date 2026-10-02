"""Document retrieval endpoint."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.application.retrieval import RetrievalService
from app.infrastructure.vector_store.runtime import (
    get_embedding_provider,
    get_vector_store,
)


class SearchRequest(BaseModel):
    """Payload for semantic document search."""

    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=4, ge=1, le=20)
    min_score: float = Field(default=0.0, ge=-1.0, le=1.0)
    document_id: str | None = None
    page_number: int | None = Field(default=None, ge=1)


class SearchResultResponse(BaseModel):
    """A retrieved chunk and its source metadata."""

    chunk_id: str
    content: str
    score: float
    document_id: str
    page_number: int
    chunk_index: int


router = APIRouter(prefix="/documents", tags=["retrieval"])


def get_retrieval_service() -> RetrievalService:
    """Build retrieval from the configured embedding and vector ports."""

    return RetrievalService(get_embedding_provider(), get_vector_store())


@router.post("/search", response_model=list[SearchResultResponse])
def search_documents(
    request: SearchRequest,
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
) -> list[SearchResultResponse]:
    """Return semantically relevant chunks and their source metadata."""

    metadata_filter: dict[str, str] = {}
    if request.document_id:
        metadata_filter["document_id"] = request.document_id
    if request.page_number is not None:
        metadata_filter["page_number"] = str(request.page_number)

    results = retrieval_service.search(
        query=request.query,
        limit=request.limit,
        min_score=request.min_score,
        metadata_filter=metadata_filter or None,
    )
    return [
        SearchResultResponse(
            chunk_id=result.chunk.chunk_id,
            content=result.chunk.content,
            score=result.score,
            document_id=result.chunk.document_id,
            page_number=result.chunk.page_number,
            chunk_index=result.chunk.chunk_index,
        )
        for result in results
    ]
