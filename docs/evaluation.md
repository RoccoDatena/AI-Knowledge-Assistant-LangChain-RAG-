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
and the expected relevant chunk IDs. The current test suite uses a deterministic
fake retriever; a future evaluation dataset can use real document fixtures.

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


