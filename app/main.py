from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import agent, tools
from app.services.retriever import get_collection, seed_corpus_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Idempotent Chroma seeding at startup
    seed_corpus_if_empty()
    yield


app = FastAPI(
    title="Tideline Research Assistant API",
    description="ReAct Agent REST API answering queries over Tideline documentation corpus.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent.router)
app.include_router(tools.router)


@app.get("/health", tags=["System"])
def health_check():
    """Genuine health check reporting system readiness and ChromaDB document count."""
    try:
        col = get_collection()
        doc_count = col.count()
        return {
            "status": "healthy",
            "collection_name": col.name,
            "indexed_chunks": doc_count,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }
