"""Generate embeddings using OpenAI's API with batching."""

import os
from openai import OpenAI

EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
BATCH_SIZE = 100  # OpenAI supports up to 2048 inputs, but 100 is safe for rate limits

client = OpenAI()  # reads OPENAI_API_KEY from env


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts in batches. Returns one vector per input text."""
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        # Response embeddings are in the same order as inputs
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)
        print(f"  Embedded {min(i + BATCH_SIZE, len(texts))}/{len(texts)}")

    return all_embeddings
