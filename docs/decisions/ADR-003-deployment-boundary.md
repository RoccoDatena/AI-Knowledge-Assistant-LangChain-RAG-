# ADR-003: Keep cloud deployment opt-in

## Status

Accepted

## Decision

The local project must run without AWS, Docker, Ollama, or paid AI APIs.
Cloud deployment remains documented but is not provisioned automatically.

## Rationale

The project must remain free for learning and portfolio development. Cloud
services, hosted vector stores, and model inference can generate costs and
require separate security and budget controls.

## Consequences

- AWS architecture is visible to recruiters without accidental charges.
- Local adapters and cloud adapters must share the same ports.
- A future deployment milestone will require an explicit cost and security
  review before implementation.
