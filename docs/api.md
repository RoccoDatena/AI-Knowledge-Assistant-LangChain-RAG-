# API guide

Start the server with:

```powershell
uvicorn app.main:app --reload
```

The canonical interactive contract is available at:

```text
http://127.0.0.1:8000/docs
```

`GET /health` is the liveness check. `GET /health/ready` validates the active
configuration and reports `503` when the service is not ready to receive
traffic.

## Typical workflow

```text
POST /documents/upload
POST /documents/index
POST /conversations
POST /conversations/{id}/messages
GET  /conversations/{id}/history
```

The chat response includes `grounded` and `sources`. If no relevant context
is found, `grounded` is false and `sources` is empty.

## Error contract

Errors use a stable envelope so clients can branch on `code` instead of
parsing human-readable messages:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Conversation not found",
    "details": null,
    "request_id": "a-request-correlation-id"
  }
}
```

Validation failures use `VALIDATION_ERROR` and include field-level details.
Uploading identical PDF content returns `409 CONFLICT` with code `CONFLICT`.
