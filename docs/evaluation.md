# Retrieval evaluation

The project includes a small offline evaluator in
`app/application/evaluation.py`. It measures retrieval independently from the
LLM, which makes provider and embedding comparisons reproducible.

## Metrics

- **Hit@K**: percentage of queries where at least one relevant chunk appears
  in the first `K` results.
- **MRR**: average reciprocal rank of the first relevant chunk. A result in
  position one scores `1.0`; position two scores `0.5`.

The evaluator accepts a list of `RetrievalExample` objects containing a query
and the expected relevant chunk IDs. The versioned dataset contains eight
queries across ingestion, safety, operations, and architecture scenarios. The
chunk IDs are intentionally explicit so the same benchmark can be reused with
different retriever implementations.

The JSON dataset contract is demonstrated in
`evaluation/retrieval_examples.json` and can be loaded with
`load_retrieval_examples`.

## Run the evaluation

From the repository root:

```powershell
python -m scripts.evaluate_retrieval
python -m scripts.evaluate_retrieval --dataset evaluation/retrieval_examples.json --k 4
```

The command prints machine-readable JSON containing the number of examples,
Hit@K, and MRR. With an empty local knowledge base, zero scores are expected.

## Verify semantic embeddings

After installing `requirements-embeddings.txt` and setting
`EMBEDDING_PROVIDER=sentence_transformers`, run:

```powershell
python -m scripts.check_semantic_embeddings
```

The first execution downloads the configured model if it is not already in the
Hugging Face cache.
## Evaluate the bundled offline corpus

The repository includes `evaluation/corpus.json`, a small deterministic corpus
with eight chunks matching the benchmark queries. Evaluate it without using the
persistent application data:

```powershell
$env:EMBEDDING_PROVIDER="hashing"
python -m scripts.evaluate_retrieval --corpus evaluation/corpus.json
```

This mode is fully offline and reproducible. It is useful for comparing vector
store or embedding adapters before evaluating a real document collection.
### Observed fixture results

On the bundled corpus, the current local checks produce:

| Embedding provider | Hit@4 | MRR |
| --- | ---: | ---: |
| Hashing baseline | 1.00 | 0.8229 |
| `all-MiniLM-L6-v2` | 1.00 | 0.8750 |

These values are reference measurements for the synthetic corpus, not a claim
about production document quality. A real evaluation set should be added before
making model or provider decisions.
