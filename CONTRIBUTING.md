# Contributing

Thanks for contributing to AI Knowledge Assistant.

## Local workflow

1. Create and activate a Python 3.13 virtual environment.
2. Install the dependencies from `requirements.txt`.
3. Copy `.env.example` to `.env` and keep secrets out of Git.
4. Run the quality checks before opening a pull request:

```powershell
ruff check .
ruff format --check .
mypy app
pytest -q
```

On Windows, `.\scripts\quality-check.ps1` runs the same sequence.

## Pull requests

- Keep changes focused and explain the architectural motivation.
- Add or update tests for behavioral changes.
- Update documentation when an API, configuration value, or deployment
  decision changes.
- Do not commit API keys, user documents, generated data, or local settings.

## Commit guidance

Use concise imperative messages, for example:

```text
Add document indexing endpoint
```
