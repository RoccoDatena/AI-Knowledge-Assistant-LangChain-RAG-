"""Verify the configured semantic embedding provider."""

from app.infrastructure.vector_store.runtime import get_embedding_provider


def main() -> None:
    """Create one embedding and print basic provider diagnostics."""

    provider = get_embedding_provider()
    vector = provider.embed_query("domanda di verifica sugli embeddings")
    squared_norm = sum(value * value for value in vector)
    print(f"provider={type(provider).__name__}")
    print(f"dimensions={len(vector)}")
    print(f"normalized={round(squared_norm, 4)}")


if __name__ == "__main__":
    main()
