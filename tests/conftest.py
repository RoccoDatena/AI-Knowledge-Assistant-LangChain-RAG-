"""Test-suite environment defaults."""

import os

# Tests stay deterministic and lightweight even when the developer .env
# enables a local semantic embedding model for manual runs.
os.environ["EMBEDDING_PROVIDER"] = "hashing"
