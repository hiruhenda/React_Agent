import os
import hashlib
from datetime import datetime, timezone
from typing import List, Optional
import chromadb
from sentence_transformers import SentenceTransformer
from app.schemas.tools import (
    DocumentChunk,
    RetrieveResponse,
    IngestResponse,
    CollectionStats,
)

COLLECTION_NAME = "tideline_docs"
CHROMA_PERSIST_DIR = "chroma_db"

_client: Optional[chromadb.PersistentClient] = None
_collection = None
_embedder: Optional[SentenceTransformer] = None


def get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _embedder


def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def sliding_window_chunk(text: str, chunk_size: int = 600, overlap: int = 100) -> List[str]:
    cleaned = text.strip()
    if not cleaned:
        return []
    chunks = []
    start = 0
    while start < len(cleaned):
        end = start + chunk_size
        chunk = cleaned[start:end]
        chunks.append(chunk)
        if end >= len(cleaned):
            break
        start += (chunk_size - overlap)
    return chunks


def ingest_document(
    filename: str,
    content: str,
    overwrite: bool = True,
    chunk_size: int = 600,
    overlap: int = 100,
) -> IngestResponse:
    """Ingests a document with sliding window chunks, source metadata, and stats."""
    collection = get_collection()
    embedder = get_embedder()

    cleaned_content = content.strip()
    if not cleaned_content:
        raise ValueError("Cannot ingest empty document or file with no extractable text.")

    doc_id = hashlib.md5(filename.encode("utf-8")).hexdigest()[:12]

    existing = collection.get(where={"source_filename": filename})
    if existing and existing["ids"]:
        if not overwrite:
            stats = get_collection_stats()
            return IngestResponse(
                document_id=doc_id,
                source_filename=filename,
                chunk_count=len(existing["ids"]),
                collection_stats=stats,
                message=f"Document '{filename}' already exists. Overwrite was false.",
            )
        collection.delete(where={"source_filename": filename})

    chunks = sliding_window_chunk(cleaned_content, chunk_size=chunk_size, overlap=overlap)
    if not chunks:
        raise ValueError("Document yielded 0 chunks after splitting.")

    now_iso = datetime.now(timezone.utc).isoformat()
    embeddings = embedder.encode(chunks).tolist()

    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "source_filename": filename,
            "chunk_index": i,
            "ingested_at": now_iso,
            "doc_id": doc_id,
        }
        for i in range(len(chunks))
    ]

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    stats = get_collection_stats()
    return IngestResponse(
        document_id=doc_id,
        source_filename=filename,
        chunk_count=len(chunks),
        collection_stats=stats,
        message=f"Successfully ingested {len(chunks)} chunks from '{filename}'.",
    )


def get_collection_stats() -> CollectionStats:
    collection = get_collection()
    total = collection.count()
    if total == 0:
        return CollectionStats(total_chunks=0, unique_documents=0)

    all_docs = collection.get(include=["metadatas"])
    sources = set()
    if all_docs and all_docs.get("metadatas"):
        for m in all_docs["metadatas"]:
            if m and "source_filename" in m:
                sources.add(m["source_filename"])

    return CollectionStats(
        total_chunks=total,
        unique_documents=len(sources),
    )


def retrieve_documents(
    query: str,
    top_k: int = 3,
    source_filter: Optional[str] = None,
) -> RetrieveResponse:
    """Performs semantic similarity search with optional source filtering."""
    cleaned_query = query.strip()
    if not cleaned_query:
        return RetrieveResponse(query=query, results=[], total_found=0)

    collection = get_collection()
    if collection.count() == 0:
        return RetrieveResponse(query=cleaned_query, results=[], total_found=0)

    embedder = get_embedder()
    query_emb = embedder.encode([cleaned_query]).tolist()

    where_clause = {"source_filename": source_filter} if source_filter else None

    fetch_k = min(top_k, collection.count())
    query_kwargs = {
        "query_embeddings": query_emb,
        "n_results": fetch_k,
    }
    if where_clause:
        query_kwargs["where"] = where_clause

    raw_results = collection.query(**query_kwargs)

    chunks: List[DocumentChunk] = []
    if raw_results and raw_results.get("documents"):
        docs = raw_results["documents"][0]
        metadatas = raw_results["metadatas"][0] if raw_results.get("metadatas") else [{}] * len(docs)
        distances = raw_results["distances"][0] if raw_results.get("distances") else [0.0] * len(docs)

        for i, text in enumerate(docs):
            meta = metadatas[i] or {}
            score = distances[i]
            similarity = round(1.0 - score, 4) if score is not None else 0.0

            filename = meta.get("source_filename") or meta.get("source", "unknown")
            chunk_idx = meta.get("chunk_index") or meta.get("chunk_id", i)

            chunks.append(
                DocumentChunk(
                    source_filename=filename,
                    chunk_index=chunk_idx,
                    content=text,
                    score=similarity,
                )
            )

    return RetrieveResponse(
        query=cleaned_query,
        results=chunks,
        total_retrieved=len(chunks),
    )