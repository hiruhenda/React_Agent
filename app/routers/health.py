from fastapi import APIRouter, status
from app.schemas.agent import HealthResponse
from app.services.retriever import get_collection

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def check_health():
    """Performs genuine connectivity verification on ChromaDB datastore."""
    try:
        coll = get_collection()
        count = coll.count()
        return HealthResponse(
            status="ok",
            datastore_connected=True,
            collection_size=count
        )
    except Exception:
        return HealthResponse(
            status="unhealthy",
            datastore_connected=False,
            collection_size=0
        )
