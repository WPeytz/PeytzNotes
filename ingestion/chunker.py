"""Split notes into ~500 token chunks, preserving heading context."""

import re
from dataclasses import dataclass
import tiktoken

# Use the tokenizer that matches OpenAI embedding models
_enc = tiktoken.get_encoding("cl100k_base")

TARGET_TOKENS = 500
MAX_TOKENS = 800
OVERLAP_SENTENCES = 2  # repeat last N sentences for context continuity


@dataclass
class Chunk:
    text: str
    heading: str | None
    chunk_index: int
    token_count: int


def count_tokens(text: str) -> int:
    return len(_enc.encode(text))


def split_into_sections(content: str) -> list[tuple[str | None, str]]:
    """Split markdown by headings into (heading, body) pairs."""
    # Match lines starting with 1-4 # characters
    heading_pattern = re.compile(r"^(#{1,4})\s+(.+)$", re.MULTILINE)

    sections: list[tuple[str | None, str]] = []
    last_end = 0
    current_heading = None

    for match in heading_pattern.finditer(content):
        # Save text before this heading as part of the previous section
        text_before = content[last_end:match.start()].strip()
        if text_before:
            sections.append((current_heading, text_before))

        current_heading = match.group(2).strip()
        last_end = match.end()

    # Don't forget the text after the last heading
    remaining = content[last_end:].strip()
    if remaining:
        sections.append((current_heading, remaining))

    # If no headings were found, return the whole content as one section
    if not sections and content.strip():
        sections.append((None, content.strip()))

    return sections


def split_text_into_chunks(text: str, heading: str | None, start_index: int) -> list[Chunk]:
    """Split a section's text into token-limited chunks with sentence overlap."""
    # Split into sentences (keep delimiters attached)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks: list[Chunk] = []
    current_sentences: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)

        # If adding this sentence would exceed max, finalize the current chunk
        if current_tokens + sentence_tokens > MAX_TOKENS and current_sentences:
            chunk_text = " ".join(current_sentences)
            chunks.append(Chunk(
                text=chunk_text,
                heading=heading,
                chunk_index=start_index + len(chunks),
                token_count=count_tokens(chunk_text),
            ))
            # Overlap: keep last N sentences for continuity
            current_sentences = current_sentences[-OVERLAP_SENTENCES:]
            current_tokens = count_tokens(" ".join(current_sentences))

        current_sentences.append(sentence)
        current_tokens += sentence_tokens

    # Final chunk from remaining sentences
    if current_sentences:
        chunk_text = " ".join(current_sentences)
        chunks.append(Chunk(
            text=chunk_text,
            heading=heading,
            chunk_index=start_index + len(chunks),
            token_count=count_tokens(chunk_text),
        ))

    return chunks


def chunk_note(title: str, content: str) -> list[Chunk]:
    """Chunk a full note into retrieval-ready pieces.

    Each chunk gets a heading prefix for context, e.g.:
    "Title: My Note | Section: Key Concepts\n\n<chunk text>"
    """
    sections = split_into_sections(content)
    all_chunks: list[Chunk] = []

    for heading, body in sections:
        # Build a context prefix so the chunk is self-contained
        prefix_parts = [f"Title: {title}"]
        if heading:
            prefix_parts.append(f"Section: {heading}")
        prefix = " | ".join(prefix_parts) + "\n\n"

        raw_chunks = split_text_into_chunks(body, heading, start_index=len(all_chunks))

        for chunk in raw_chunks:
            chunk.text = prefix + chunk.text
            chunk.token_count = count_tokens(chunk.text)

        all_chunks.extend(raw_chunks)

    return all_chunks
