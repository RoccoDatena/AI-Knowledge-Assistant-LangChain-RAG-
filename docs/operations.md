# Operations runbook

## Health checks

- `GET /health` verifies that the API process is responding.
- `GET /health/ready` verifies configuration readiness.
- Every response includes `X-Request-ID`; use it to correlate an error with
  structured application logs.

## Local data

The default JSON persistence lives below `data/`:

- `uploads/`: uploaded PDF files
- `documents/`: document metadata
- `conversations/`: conversation history
- `vector_store/`: persisted vectors and chunks

These files are local application state and are excluded from Git. Back them
up before any manual maintenance. Production deployments should replace this
storage with managed or transactional persistence.

## Troubleshooting

1. Check `GET /health`.
2. Check `GET /health/ready` for configuration failures.
3. Capture the `X-Request-ID` from the failing response.
4. Inspect the API JSON logs for the same identifier.
5. Confirm that `.env` uses `LLM_PROVIDER=mock` for an offline smoke test.

Provider failures return `502 PROVIDER_ERROR`; validation failures return
`422 VALIDATION_ERROR`. Neither response exposes stack traces.

## Container operation

When Docker is available, `docker compose up --build` starts the API and
frontend. The API healthcheck controls frontend startup, and the `app-data`
volume preserves local state across container restarts.
