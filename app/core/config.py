"""Environment-backed application settings."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    llm_provider: str = "mock"
    openrouter_api_key: str | None = None
    openrouter_model: str = "openrouter/free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    request_timeout_seconds: float = 30.0
    data_directory: str = "data"
    rag_min_score: float = 0.15
    rag_require_lexical_evidence: bool = True
    max_upload_bytes: int = 10 * 1024 * 1024
    vector_store: str = "json"
    embedding_provider: str = "hashing"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_local_files_only: bool = False

    def validate(self) -> "Settings":
        """Validate settings before application services use them."""

        if self.llm_provider not in {"mock", "openrouter"}:
            raise ValueError(f"Unsupported LLM_PROVIDER: {self.llm_provider}")
        if self.llm_provider == "openrouter" and not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY is required for openrouter")
        if self.vector_store not in {"json", "memory", "chroma"}:
            raise ValueError(f"Unsupported VECTOR_STORE: {self.vector_store}")
        if self.embedding_provider not in {"hashing", "sentence_transformers"}:
            raise ValueError(
                f"Unsupported EMBEDDING_PROVIDER: {self.embedding_provider}"
            )
        if self.request_timeout_seconds <= 0:
            raise ValueError("REQUEST_TIMEOUT_SECONDS must be positive")
        if not 0.0 <= self.rag_min_score <= 1.0:
            raise ValueError("RAG_MIN_SCORE must be between 0 and 1")
        if self.max_upload_bytes <= 0:
            raise ValueError("MAX_UPLOAD_BYTES must be positive")
        return self


def get_settings() -> Settings:
    """Return the current application settings."""

    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "mock"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        openrouter_model=os.getenv("OPENROUTER_MODEL", "openrouter/free"),
        openrouter_base_url=os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ),
        request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30")),
        data_directory=os.getenv("DATA_DIRECTORY", "data"),
        rag_min_score=float(os.getenv("RAG_MIN_SCORE", "0.15")),
        rag_require_lexical_evidence=os.getenv(
            "RAG_REQUIRE_LEXICAL_EVIDENCE", "true"
        ).lower()
        in {"1", "true", "yes", "on"},
        max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024))),
        vector_store=os.getenv("VECTOR_STORE", "json"),
        embedding_provider=os.getenv("EMBEDDING_PROVIDER", "hashing"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        embedding_local_files_only=os.getenv(
            "EMBEDDING_LOCAL_FILES_ONLY", "false"
        ).lower()
        in {"1", "true", "yes", "on"},
    ).validate()
