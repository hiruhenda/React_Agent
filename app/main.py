from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import agent, ingest, tools, health
from app.services.retriever import get_collection

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize ChromaDB datastore once at startup
    get_collection()
    yield

app = FastAPI(
    title="Halcyon Research Assistant Agent API",
    description="ReAct Agent REST API answering queries over Tideline corpus with semantic retrieval, calculator, and factual search tools.",
    version="1.0.0",
    lifespan=lifespan,
)

# Register routers
app.include_router(agent.router)
app.include_router(ingest.router)
app.include_router(tools.router)
app.include_router(health.router)
