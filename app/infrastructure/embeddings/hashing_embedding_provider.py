"""Small deterministic embeddings with no downloaded model."""

import hashlib
import math
import re


class HashingEmbeddingProvider:
    """Create normalized token-hash vectors as a lightweight baseline."""

    def __init__(self, dimensions: int = 256) -> None:
        if dimensions < 32:
            raise ValueError("Embedding dimensions must be at least 32")
        self._dimensions = dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple documents deterministically."""

        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        """Embed a text using signed token hashing and L2 normalization."""

        vector = [0.0] * self._dimensions
        tokens = re.findall(r"\w+", text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self._dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]
