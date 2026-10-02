"""Run the offline retrieval evaluation from the command line."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from app.application.evaluation import RetrievalEvaluator
from app.application.evaluation_corpus import load_evaluation_corpus
from app.application.evaluation_dataset import load_retrieval_examples
from app.application.retrieval import RetrievalService
from app.infrastructure.vector_store.in_memory_vector_store import InMemoryVectorStore
from app.infrastructure.vector_store.runtime import (
    get_embedding_provider,
    get_vector_store,
)


def main() -> None:
    """Load examples, evaluate the configured retriever, and print JSON."""

    parser = argparse.ArgumentParser(description="Evaluate document retrieval")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("evaluation/retrieval_examples.json"),
        help="Path to the retrieval evaluation dataset",
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        help="Optional JSON corpus to evaluate without persistent application data",
    )
    parser.add_argument(
        "--k", type=int, default=4, help="Number of results to evaluate"
    )
    args = parser.parse_args()

    examples = load_retrieval_examples(args.dataset)
    embedding_provider = get_embedding_provider()
    if args.corpus:
        vector_store = InMemoryVectorStore()
        chunks = load_evaluation_corpus(args.corpus)
        vector_store.add(
            chunks,
            embedding_provider.embed_documents([chunk.content for chunk in chunks]),
        )
    else:
        vector_store = get_vector_store()
    service = RetrievalService(embedding_provider, vector_store)
    result = RetrievalEvaluator(service).evaluate(examples, k=args.k)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
