import os
import json
import hashlib
from pathlib import Path
from typing import Optional, List

import faiss
import numpy as np
import tiktoken
from flask import Blueprint, request, jsonify, current_app

libraries_bp = Blueprint("libraries", __name__)


def _chunk_text(content: str, max_tokens: int = 500, overlap: int = 50) -> List[str]:
    """Split text into token-aware chunks.

    Uses tiktoken for tokenization so chunking is closer to the eventual
    embedding input. Overlap ensures context continuity.
    """

    try:
        encoding = tiktoken.get_encoding("cl100k_base")
    except Exception:
        # Fallback to the first available encoding if cl100k_base is not present
        encoding = tiktoken.get_encoding(tiktoken.list_encoding_names()[0])

    tokens = encoding.encode(content)
    if not tokens:
        return [content]

    chunks: List[str] = []

    if max_tokens <= 0:
        return [content]

    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append(encoding.decode(chunk_tokens))
        # Prevent infinite loop if overlap is misconfigured
        if max_tokens <= overlap:
            break
        start += max_tokens - overlap

    return chunks


def _embed_chunk(text: str, dimension: int = 384) -> np.ndarray:
    """Create a deterministic embedding vector for the given text.

    For local/offline use we derive a random-but-repeatable vector from the
    SHA-256 hash of the text. Vectors are normalized to unit length.
    """

    seed_bytes = hashlib.sha256(text.encode("utf-8")).digest()[:8]
    seed = int.from_bytes(seed_bytes, "big", signed=False)
    rng = np.random.default_rng(seed)
    vec = rng.normal(size=dimension).astype("float32")
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec


def _load_or_create_index(index_path: Path, dimension: int) -> faiss.IndexFlatL2:
    """Load an existing FAISS index from disk or create a new one.

    Raises a ValueError when the on-disk index dimension differs from the
    expected dimension so uploads do not silently corrupt the vector store.
    """

    if index_path.exists():
        index = faiss.read_index(str(index_path))
        if index.d != dimension:
            raise ValueError(
                f"Existing index at {index_path} has dimension {index.d}, expected {dimension}"
            )
        return index

    index_path.parent.mkdir(parents=True, exist_ok=True)
    return faiss.IndexFlatL2(dimension)


def _persist_index(index: faiss.IndexFlatL2, index_path: Path):
    index_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path))


def _append_metadata(metadata_path: Path, start_id: int, chunks: List[str], file_path: Path, metadata: Optional[dict] = None):
    """Append JSONL metadata entries describing each chunk."""

    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, "a", encoding="utf-8") as meta_file:
        for idx, chunk in enumerate(chunks):
            entry = {
                "id": start_id + idx,
                "file": str(file_path),
                "chunk_index": idx,
                "text": chunk,
            }
            if metadata:
                entry["metadata"] = metadata
            meta_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _vectorize_and_store(
    tool_id: str,
    file_path: Path,
    content: str,
    metadata: Optional[dict] = None,
    *,
    max_tokens: int = 500,
    overlap: int = 50,
):
    """Chunk and vectorize content, persisting results to a FAISS index."""

    chunks = _chunk_text(content, max_tokens=max_tokens, overlap=overlap)
    vectors = np.vstack([_embed_chunk(chunk) for chunk in chunks]).astype("float32")

    index_dir = Path(current_app.root_path) / "data" / "vector_stores" / tool_id
    index_path = index_dir / "faiss.index"
    metadata_path = index_dir / "metadata.jsonl"

    index = _load_or_create_index(index_path, vectors.shape[1])
    start_id = index.ntotal
    index.add(vectors)
    _persist_index(index, index_path)
    _append_metadata(metadata_path, start_id, chunks, file_path, metadata)

    return {
        "chunks": len(chunks),
        "dimension": vectors.shape[1],
        "index_size": index.ntotal,
        "index_path": str(index_path.relative_to(current_app.root_path)),
        "metadata_path": str(metadata_path.relative_to(current_app.root_path)),
        "chunk_size": max_tokens,
        "chunk_overlap": overlap,
    }


@libraries_bp.route("/<tool_id>/libraries", methods=["POST"])
def add_library_file(tool_id):
    """Add (save) a file for the given tool_id.

    Expects JSON body:
      {
        "filename": "example.txt",
        "content": "file content as string",
        "metadata": {"optional": "object"},
        "chunk_size": 500,           # optional, defaults to 500 tokens
        "chunk_overlap": 50          # optional, defaults to 50 tokens
      }

    Saves file to: data/libraries/<tool_id>/<filename>
    Returns 201 with saved path on success.
    """
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400

    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "Invalid JSON payload"}), 400

    filename = payload.get("filename")
    content = payload.get("content")
    metadata: Optional[dict] = payload.get("metadata")
    chunk_size = payload.get("chunk_size", 500)
    chunk_overlap = payload.get("chunk_overlap", 50)

    if not filename or not isinstance(filename, str):
        return jsonify({"error": "filename is required and must be a string"}), 400
    if content is None or not isinstance(content, str):
        return jsonify({"error": "content is required and must be a string"}), 400
    if not isinstance(chunk_size, int) or chunk_size <= 0:
        return jsonify({"error": "chunk_size must be a positive integer"}), 400
    if not isinstance(chunk_overlap, int) or chunk_overlap < 0:
        return jsonify({"error": "chunk_overlap must be a non-negative integer"}), 400
    if chunk_overlap >= chunk_size:
        return jsonify({"error": "chunk_overlap must be smaller than chunk_size"}), 400

    # metadata is optional; if provided it should be a dict
    if metadata is not None and not isinstance(metadata, dict):
        return jsonify({"error": "metadata must be an object/dictionary if provided"}), 400

    # sanitize filename a little (avoid absolute paths)
    filename = os.path.basename(filename)

    base_dir = Path(current_app.root_path) / "data" / "libraries" / tool_id
    try:
        base_dir.mkdir(parents=True, exist_ok=True)
        file_path = base_dir / filename
        with open(file_path, "w", encoding="utf-8") as fh:
            fh.write(content)

        # If metadata was provided, save a sidecar JSON file alongside the saved file.
        meta_to_write = None
        if metadata:
            meta_path = base_dir / (filename + ".metadata.json")
            # enrich metadata with some auto fields if not present
            meta_to_write = dict(metadata)  # copy
            meta_to_write.setdefault("uploaded_by", payload.get("uploaded_by", "anonymous"))
            meta_to_write.setdefault("filename", filename)
            meta_to_write.setdefault("tool_id", tool_id)
            meta_to_write.setdefault("saved_at", None)
            # set saved_at now as ISO timestamp
            from datetime import datetime

            meta_to_write["saved_at"] = datetime.utcnow().isoformat() + "Z"

            with open(meta_path, "w", encoding="utf-8") as mh:
                json.dump(meta_to_write, mh, ensure_ascii=False, indent=2)

        vectorization = _vectorize_and_store(
            tool_id,
            file_path,
            content,
            meta_to_write,
            max_tokens=chunk_size,
            overlap=chunk_overlap,
        )

    except ValueError as exc:
        return jsonify({"error": "invalid_request", "details": str(exc)}), 400
    except Exception as exc:
        current_app.logger.exception("Failed to save library file or metadata")
        return jsonify({"error": "failed_to_save", "details": str(exc)}), 500

    return (
        jsonify({
            "status": "created",
            "path": str(file_path.relative_to(current_app.root_path)),
            "metadata_path": str((base_dir / (filename + ".metadata.json")).relative_to(current_app.root_path)) if metadata else None,
            "vector_store": vectorization,
        }),
        201,
    )
