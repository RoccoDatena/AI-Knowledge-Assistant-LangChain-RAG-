"""Tests for PDF upload and document metadata endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.pdf.pypdf_text_extractor import (
    ExtractedPage,
    PdfExtractionError,
    PypdfTextExtractor,
)
from app.infrastructure.persistence.json_document_repository import (
    JsonDocumentRepository,
)
from app.interfaces.api.document_routes import (
    get_document_repository,
    get_pdf_extractor,
)
from app.main import app


class FakePdfExtractor:
    """Small test double that avoids generating a binary PDF fixture."""

    def extract(self, content: bytes) -> list[ExtractedPage]:
        assert content == b"%PDF-fake"
        return [ExtractedPage(page_number=1, text="Contenuto di test")]


def test_upload_pdf_stores_file_and_metadata(tmp_path: Path, monkeypatch) -> None:
    """A valid PDF upload should create both the binary and metadata record."""

    monkeypatch.chdir(tmp_path)
    app.dependency_overrides[get_document_repository] = lambda: JsonDocumentRepository(
        Path("data/documents")
    )
    app.dependency_overrides[get_pdf_extractor] = FakePdfExtractor

    try:
        with TestClient(app) as client:
            response = client.post(
                "/documents/upload",
                files={"file": ("manual.pdf", b"%PDF-fake", "application/pdf")},
            )
            documents = client.get("/documents")

        assert response.status_code == 201
        payload = response.json()
        assert payload["filename"] == "manual.pdf"
        assert payload["page_count"] == 1
        assert payload["text_length"] == len("Contenuto di test")
        assert len(documents.json()) == 1
        assert list((tmp_path / "data" / "uploads").glob("*.pdf"))
    finally:
        app.dependency_overrides.clear()


def test_upload_rejects_non_pdf() -> None:
    """Non-PDF files should be rejected before extraction."""

    with TestClient(app) as client:
        response = client.post(
            "/documents/upload",
            files={"file": ("notes.txt", b"text", "text/plain")},
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BAD_REQUEST"
    assert response.json()["error"]["message"] == "Only PDF files are supported"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_real_pdf_extractor_wraps_invalid_content() -> None:
    """Invalid binary input should become a stable extraction error."""

    with pytest.raises(PdfExtractionError, match="Unable to read PDF"):
        PypdfTextExtractor().extract(b"not a pdf")


def test_upload_rejects_oversized_content(tmp_path: Path, monkeypatch) -> None:
    """Oversized uploads should be rejected before PDF extraction."""

    monkeypatch.chdir(tmp_path)
    app.dependency_overrides[get_document_repository] = lambda: JsonDocumentRepository(
        Path("data/documents")
    )
    app.dependency_overrides[get_pdf_extractor] = FakePdfExtractor

    try:
        with TestClient(app) as client:
            response = client.post(
                "/documents/upload",
                files={
                    "file": (
                        "large.pdf",
                        b"x" * (10 * 1024 * 1024 + 1),
                        "application/pdf",
                    )
                },
            )

        assert response.status_code == 413
        assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
    finally:
        app.dependency_overrides.clear()


def test_upload_rejects_pdf_extension_with_invalid_signature() -> None:
    """A PDF filename must also contain the PDF file signature."""

    with TestClient(app) as client:
        response = client.post(
            "/documents/upload",
            files={"file": ("spoofed.pdf", b"not a pdf", "application/pdf")},
        )

    assert response.status_code == 400
    assert response.json()["error"]["message"] == "Uploaded file is not a valid PDF"


def test_upload_rejects_duplicate_content(tmp_path: Path) -> None:
    """The same PDF content should not create duplicate knowledge entries."""

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.chdir(tmp_path)
    app.dependency_overrides[get_document_repository] = lambda: JsonDocumentRepository(
        Path("data/documents")
    )
    app.dependency_overrides[get_pdf_extractor] = FakePdfExtractor

    try:
        with TestClient(app) as client:
            first = client.post(
                "/documents/upload",
                files={"file": ("first.pdf", b"%PDF-fake", "application/pdf")},
            )
            duplicate = client.post(
                "/documents/upload",
                files={"file": ("renamed.pdf", b"%PDF-fake", "application/pdf")},
            )

        assert first.status_code == 201
        assert duplicate.status_code == 409
        assert duplicate.json()["error"]["code"] == "CONFLICT"
    finally:
        app.dependency_overrides.clear()
        monkeypatch.undo()


def test_upload_normalizes_untrusted_filename(tmp_path: Path) -> None:
    """Client path components must not affect the stored upload location."""

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.chdir(tmp_path)
    app.dependency_overrides[get_document_repository] = lambda: JsonDocumentRepository(
        Path("data/documents")
    )
    app.dependency_overrides[get_pdf_extractor] = FakePdfExtractor

    try:
        with TestClient(app) as client:
            response = client.post(
                "/documents/upload",
                files={
                    "file": ("..\\..\\outside.pdf", b"%PDF-fake", "application/pdf")
                },
            )

        assert response.status_code == 201
        assert response.json()["filename"] == "outside.pdf"
        stored_files = list((tmp_path / "data" / "uploads").glob("*.pdf"))
        assert len(stored_files) == 1
        assert stored_files[0].parent == tmp_path / "data" / "uploads"
    finally:
        app.dependency_overrides.clear()
        monkeypatch.undo()
