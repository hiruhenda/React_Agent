import os
import glob
from typing import List, Optional
import chromadb
from chromadb.utils import embedding_functions
from app.schemas.tools import DocumentChunk

_CHROMA_DIR = os.path.abspath(os.path.join("chroma_db"))
_COLLECTION_NAME = "tideline_docs"
_client: Optional[chromadb.PersistentClient] = None
_collection = None


def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=_CHROMA_DIR)
        emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        _collection = _client.get_or_create_collection(
            name=_COLLECTION_NAME,
            embedding_function=emb_fn,
        )
    return _collection


def seed_corpus_if_empty(chunk_size: int = 600, overlap: int = 100):
    """Idempotently seeds markdown documents from corpus/ into ChromaDB if empty."""
    col = get_collection()
    if col.count() > 0:
        return

    corpus_files = glob.glob(os.path.join("corpus", "*.md"))
    doc_ids = []
    texts = []
    metadatas = []

    for filepath in sorted(corpus_files):
        filename = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        start = 0
        idx = 0
        while start < len(content):
            end = min(start + chunk_size, len(content))
            chunk_text = content[start:end].strip()
            if chunk_text:
                chunk_id = f"{filename}_{idx}"
                doc_ids.append(chunk_id)
                texts.append(chunk_text)
                metadatas.append({
                    "source": filename,
                    "chunk_index": idx,
                })
                idx += 1
            if end >= len(content):
                break
            start += (chunk_size - overlap)

    if texts:
        col.add(
            ids=doc_ids,
            documents=texts,
            metadatas=metadatas,
        )
        print(f"[INFO] Seeded {len(texts)} chunks across {len(corpus_files)} files into ChromaDB.")


def retrieve_documents(query: str, top_k: int = 3, source_filter: Optional[str] = None) -> List[DocumentChunk]:
    """Queries ChromaDB and returns structured DocumentChunk models with metadata."""
    col = get_collection()
    
    if col.count() == 0:
        seed_corpus_if_empty()

    where_clause = {"source": source_filter} if source_filter else None

    results = col.query(
        query_texts=[query],
        n_results=top_k,
        where=where_clause,
    )

    chunks: List[DocumentChunk] = []
    if not results or not results["documents"]:
        return chunks

    docs = results["documents"][0]
    metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
    distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

    for doc, meta, dist in zip(docs, metadatas, distances):
        chunks.append(
            DocumentChunk(
                content=doc,
                source_filename=meta.get("source", "unknown"),
                score=round(float(dist), 4),
                chunk_index=meta.get("chunk_index"),
            )
        )
    return chunks
