import os
from pathlib import Path
import chromadb
from langchain.tools import tool
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.schemas.tools import RetrieveInput, RetrieveOutput, RetrievedChunk

# Disable Hugging Face symlink warnings/requirements on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

CORPUS_DIR = Path("corpus")
COLLECTION_NAME = "tideline_docs"

_vectorstore = None


def get_embedding_function():
    """Initializes local HuggingFace embeddings using a lightweight sentence transformer."""
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )


def initialize_corpus_index(force_reindex: bool = False) -> Chroma:
    """Chunks documents from corpus/ and persists them in local ChromaDB."""
    global _vectorstore
    if _vectorstore is not None and not force_reindex:
        return _vectorstore

    persist_dir = settings.chroma_persist_dir
    client = chromadb.PersistentClient(path=persist_dir)
    embedding_fn = get_embedding_function()

    existing_collections = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing_collections and not force_reindex:
        col = client.get_collection(COLLECTION_NAME)
        if col.count() > 0:
            _vectorstore = Chroma(
                client=client,
                collection_name=COLLECTION_NAME,
                embedding_function=embedding_fn,
            )
            return _vectorstore

    documents = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )

    for md_file in sorted(CORPUS_DIR.glob("*.md")):
        with open(md_file, "r", encoding="utf-8") as f:
            text = f.read()
        chunks = splitter.create_documents(
            texts=[text],
            metadatas=[{"source": md_file.name}],
        )
        documents.extend(chunks)

    _vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embedding_fn,
        client=client,
        collection_name=COLLECTION_NAME,
    )
    return _vectorstore


def retrieve_corpus(query: str, k: int = 3) -> RetrieveOutput:
    """Queries ChromaDB for the most relevant Tideline documentation chunks."""
    vs = initialize_corpus_index()
    docs_and_scores = vs.similarity_search_with_relevance_scores(query, k=k)

    retrieved_chunks = [
        RetrievedChunk(
            content=doc.page_content,
            source_document=doc.metadata.get("source", "unknown"),
            score=round(float(score), 4) if score is not None else None,
        )
        for doc, score in docs_and_scores
    ]

    return RetrieveOutput(query=query, chunks=retrieved_chunks)


@tool(args_schema=RetrieveInput)
def retrieve_tideline_docs(query: str, k: int = 3) -> str:
    """Useful for searching internal Tideline technical documentation, RFC-014,
    pricing FAQ, storage tiers, engineering guides, and postmortem incident reports.
    Do NOT use this tool for general world knowledge or arithmetic.
    """
    output = retrieve_corpus(query=query, k=k)
    if not output.chunks:
        return f"No Tideline internal documentation found matching query: '{query}'."

    formatted = []
    for idx, chunk in enumerate(output.chunks, start=1):
        score_str = f" (relevance: {chunk.score})" if chunk.score is not None else ""
        formatted.append(f"[{idx}] Source: {chunk.source_document}{score_str}\n{chunk.content}")

    return "\n\n---\n\n".join(formatted)