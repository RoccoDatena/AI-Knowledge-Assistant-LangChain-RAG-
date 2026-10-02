# Security policy

## Supported versions

Only the latest version on the default branch is currently supported.

## Reporting a vulnerability

Please do not open a public issue for a suspected security vulnerability.
Contact the repository maintainer privately through the GitHub security contact
mechanism. Include reproduction steps, affected files or endpoints, and the
potential impact.

Never include real API keys, personal data, or confidential documents in a
report.

## Current security boundaries

- `.env` and application data directories are excluded from Git.
- The API is intended for local development and portfolio demonstration.
- Authentication, authorization, rate limiting, and encrypted production
  storage are future concerns for an AWS deployment.
