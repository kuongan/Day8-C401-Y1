"""
Build vector index for Day09 lab.

Usage:
    python build_index.py
"""

from __future__ import annotations

import re
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

DOCS_DIR = Path(__file__).parent / "data" / "docs"
DB_DIR = Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "day09_docs"

CHUNK_SIZE_TOKENS = 400
CHUNK_OVERLAP_TOKENS = 80
CHUNK_SIZE_CHARS = CHUNK_SIZE_TOKENS * 4
CHUNK_OVERLAP_CHARS = CHUNK_OVERLAP_TOKENS * 4


def preprocess_document(raw_text: str, filename: str) -> dict:
    lines = raw_text.strip().split("\n")
    metadata = {
        "source": filename,
        "section": [],
        "department": "unknown",
        "effective_date": "unknown",
        "access": "internal",
    }

    content_lines = []
    header_done = False

    for line in lines:
        if not header_done:
            if line.startswith("Department:"):
                metadata["department"] = line.replace("Department:", "").strip()
            elif line.startswith("Effective Date:"):
                metadata["effective_date"] = line.replace("Effective Date:", "").strip()
            elif line.startswith("Access:"):
                metadata["access"] = line.replace("Access:", "").strip()
            elif line.startswith("==="):
                header_done = True
                content_lines.append(line)
            elif line.strip() == "" or line.isupper() or line.startswith("Source:"):
                continue
        else:
            content_lines.append(line)

    cleaned_text = "\n".join(content_lines)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
    cleaned_text = re.sub(r"[ \t]+", " ", cleaned_text)
    cleaned_text = cleaned_text.strip()

    metadata["section"] = re.findall(r"=== (.*?) ===", raw_text)

    return {"text": cleaned_text, "metadata": metadata}


def split_by_size(text: str, base_metadata: dict, section: str) -> list[dict]:
    if len(text) <= CHUNK_SIZE_CHARS:
        return [{"text": text, "metadata": {**base_metadata, "section": section}}]

    paragraphs = text.split("\n\n")
    chunks: list[dict] = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 > CHUNK_SIZE_CHARS and current_chunk:
            chunks.append(
                {
                    "text": current_chunk.strip(),
                    "metadata": {**base_metadata, "section": section},
                }
            )
            overlap = (
                current_chunk[-CHUNK_OVERLAP_CHARS:]
                if len(current_chunk) > CHUNK_OVERLAP_CHARS
                else current_chunk
            )
            current_chunk = overlap + "\n\n" + para
        else:
            current_chunk += ("\n\n" if current_chunk else "") + para

    if current_chunk.strip():
        chunks.append(
            {
                "text": current_chunk.strip(),
                "metadata": {**base_metadata, "section": section},
            }
        )

    return chunks


def chunk_document(doc: dict) -> list[dict]:
    text = doc["text"]
    base_metadata = doc["metadata"].copy()

    parts = re.split(r"(===.*?===)", text)

    chunks: list[dict] = []
    current_section = "General"
    current_text = ""

    for part in parts:
        if re.match(r"===.*?===", part):
            if current_text.strip():
                chunks.extend(split_by_size(current_text.strip(), base_metadata, current_section))
            current_section = part.strip("= ").strip()
            current_text = ""
        else:
            current_text += part

    if current_text.strip():
        chunks.extend(split_by_size(current_text.strip(), base_metadata, current_section))

    return chunks


def build_index() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(DB_DIR))

    # Recreate collection to avoid duplicate ids/inconsistent old embeddings.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    model = SentenceTransformer("all-MiniLM-L6-v2")

    total = 0
    for file_path in sorted(DOCS_DIR.glob("*.txt")):
        raw = file_path.read_text(encoding="utf-8")
        doc = preprocess_document(raw, file_path.name)
        chunks = chunk_document(doc)

        for idx, chunk in enumerate(chunks):
            embedding = model.encode([chunk["text"]])[0].tolist()
            chunk_id = f"{file_path.stem}_{idx}"
            collection.upsert(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk["text"]],
                metadatas=[chunk["metadata"]],
            )

        total += len(chunks)
        print(f"Indexed {file_path.name}: {len(chunks)} chunks")

    print(f"Done. Total chunks: {total}")


def inspect(n: int = 5) -> None:
    client = chromadb.PersistentClient(path=str(DB_DIR))
    collection = client.get_collection(COLLECTION_NAME)
    print(f"Collection count: {collection.count()}")
    result = collection.get(limit=n, include=["metadatas", "documents"])
    for i, (meta, doc) in enumerate(zip(result["metadatas"], result["documents"]), start=1):
        print(f"[{i}] source={meta.get('source')} section={meta.get('section')} date={meta.get('effective_date')}")
        print(f"    {doc[:100]}...")


if __name__ == "__main__":
    build_index()
    inspect()
