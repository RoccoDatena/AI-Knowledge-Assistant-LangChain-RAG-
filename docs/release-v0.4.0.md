# Release notes — v0.4.0

## Title

Engineering validation, grounded citations, and portfolio documentation

## Description

This release consolidates the validation work required to demonstrate the AI
Knowledge Assistant as a portfolio-grade RAG application. It adds durable
grounding metadata, improves unsupported-question handling, documents the
engineering process, and includes a reproducible LinkedIn communication draft.

## Highlights

- Persist `grounded` status and source citations in conversation history.
- Restore citations after reloading a conversation.
- Add end-to-end coverage for grounded history and source persistence.
- Reject semantically similar but unsupported context before LLM generation.
- Add offline mode for cached Sentence Transformers models to prevent network
  retry delays.
- Keep optional AI dependencies behind provider and adapter boundaries.
- Add engineering validation, troubleshooting, and reproducibility
  documentation.
- Add an English LinkedIn post draft and a prompt for a project architecture
  slide.
- Add a screenshot guide for the portfolio demo.

## Verification

- Ruff lint: passed
- Ruff format check: passed
- mypy: passed
- pytest: 59 passed
- GitHub Actions CI: passed
- Manual Streamlit smoke test: passed

## Known limitations

- The default LLM is deterministic mock output.
- OCR for scanned PDFs is not implemented.
- JSON persistence is intended for local and portfolio use, not concurrent
  production traffic.
- Free remote model availability depends on the selected provider.
