"""Text extraction from text-based PDFs using pypdf."""

from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader


class PdfExtractionError(ValueError):
    """Raised when a PDF cannot be read or contains no text."""


@dataclass(frozen=True)
class ExtractedPage:
    """Text extracted from one PDF page."""

    page_number: int
    text: str


class PypdfTextExtractor:
    """Extract page-aware text from a PDF byte stream."""

    def extract(self, content: bytes) -> list[ExtractedPage]:
        """Return non-empty pages, preserving one-based page numbers."""

        try:
            reader = PdfReader(BytesIO(content))
            pages = [
                ExtractedPage(
                    page_number=index + 1, text=(page.extract_text() or "").strip()
                )
                for index, page in enumerate(reader.pages)
            ]
        except Exception as exc:
            raise PdfExtractionError("Unable to read PDF") from exc

        non_empty_pages = [page for page in pages if page.text]
        if not non_empty_pages:
            raise PdfExtractionError("PDF contains no extractable text")
        return non_empty_pages
