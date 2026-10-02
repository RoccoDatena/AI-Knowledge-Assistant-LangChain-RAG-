# ADR-004: Keep heavyweight capabilities optional

## Status

Accepted

## Context

The project must remain free to run and lightweight on a development machine
with limited disk space. Streamlit, ChromaDB, and local embedding models are
useful capabilities, but they are not required to develop or test the backend.

## Decision

Keep dependency groups separate:

- `requirements.txt` contains backend runtime dependencies.
- `requirements-dev.txt` contains test and quality tooling.
- `requirements-frontend.txt` adds Streamlit only when the UI is needed.
- optional AI/vector adapters use lazy imports and are not enabled by default.

## Consequences

The default workflow is faster and consumes less disk space. The trade-off is
that optional features require an explicit installation step before use. This
boundary is documented in the README and Dockerfiles.
