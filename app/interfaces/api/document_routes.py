"""Document upload and metadata endpoints."""

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.application.chunking import DocumentChunker
from app.application.documents import DeleteDocumentService
from app.application.indexing import DocumentIndexer
from app.core.config import get_settings
from app.domain.entities import Document
from app.domain.ports import DocumentRepository
from app.infrastructure.pdf.pypdf_text_extractor import (
    PdfExtractionError,
    PypdfTextExtractor,
)
from app.infrastructure.persistence.json_document_repository import (
    JsonDocumentRepository,
)
from app.infrastructure.vector_store.runtime import (
    get_embedding_provider,
    get_vector_store,
)


class DocumentResponse(BaseModel):
    """Public representation of document metadata."""

    document_id: str
    filename: str
    uploaded_at: str
    page_count: int
    text_length: int


router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_repository() -> DocumentRepository:
    """Build the JSON document metadata repository."""

    return JsonDocumentRepository(Path(get_settings().data_directory) / "documents")


def get_pdf_extractor() -> PypdfTextExtractor:
    """Build the PDF text extractor."""

    return PypdfTextExtractor()


def get_document_indexer(
    repository: DocumentRepository = Depends(get_document_repository),
    extractor: PypdfTextExtractor = Depends(get_pdf_extractor),
) -> DocumentIndexer:
    """Build the indexing use case from injectable infrastructure ports."""

    return DocumentIndexer(
        document_repository=repository,
        extractor=extractor,
        chunker=DocumentChunker(),
        embedding_provider=get_embedding_provider(),
        vector_store=get_vector_store(),
    )


def get_delete_document_service(
    repository: DocumentRepository = Depends(get_document_repository),
) -> DeleteDocumentService:
    """Build the document deletion use case."""

    return DeleteDocumentService(repository, get_vector_store())


@router.post(
    "/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED
)
async def upload_document(
    file: UploadFile = File(...),
    repository: DocumentRepository = Depends(get_document_repository),
    extractor: PypdfTextExtractor = Depends(get_pdf_extractor),
) -> DocumentResponse:
    """Validate, store, and inspect a text-based PDF."""

    # Normalize both Windows and POSIX separators before taking the basename.
    filename = Path((file.filename or "").replace("\\", "/")).name
    if not filename or Path(filename).suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await _read_upload_with_limit(file, get_settings().max_upload_bytes)
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid PDF")
    document_hash = hashlib.sha256(content).hexdigest()
    if any(document.document_hash == document_hash for document in repository.list()):
        raise HTTPException(status_code=409, detail="Document already exists")

    try:
        pages = extractor.extract(content)
    except PdfExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    document_id = str(uuid4())
    upload_directory = Path(get_settings().data_directory) / "uploads"
    upload_directory.mkdir(parents=True, exist_ok=True)
    stored_path = upload_directory / f"{document_id}.pdf"
    stored_path.write_bytes(content)

    document = Document(
        document_id=document_id,
        filename=filename,
        stored_path=str(stored_path),
        uploaded_at=datetime.now(UTC),
        page_count=len(pages),
        text_length=sum(len(page.text) for page in pages),
        document_hash=document_hash,
    )
    repository.save(document)
    return _to_response(document)


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    repository: DocumentRepository = Depends(get_document_repository),
) -> list[DocumentResponse]:
    """Return metadata for all uploaded documents."""

    return [_to_response(document) for document in repository.list()]


@router.post("/index")
def index_documents(
    indexer: DocumentIndexer = Depends(get_document_indexer),
) -> dict[str, int | str]:
    """Extract and index all uploaded documents."""

    chunks_indexed = indexer.index_all()
    return {"status": "indexed", "chunks_indexed": chunks_indexed}


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    service: DeleteDocumentService = Depends(get_delete_document_service),
) -> None:
    """Delete an uploaded document and its indexed vectors."""

    if not service.delete(document_id):
        raise HTTPException(status_code=404, detail="Document not found")


def _to_response(document: Document) -> DocumentResponse:
    return DocumentResponse(
        document_id=document.document_id,
        filename=document.filename,
        uploaded_at=document.uploaded_at.isoformat(),
        page_count=document.page_count,
        text_length=document.text_length,
    )


async def _read_upload_with_limit(file: UploadFile, max_bytes: int) -> bytes:
    """Read an upload incrementally and stop when it exceeds the limit."""

    chunks: list[bytes] = []
    total_bytes = 0
    while chunk := await file.read(1024 * 1024):
        total_bytes += len(chunk)
        if total_bytes > max_bytes:
            raise HTTPException(status_code=413, detail="PDF exceeds the 10 MB limit")
        chunks.append(chunk)
    return b"".join(chunks)
