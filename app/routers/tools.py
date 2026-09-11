from fastapi import APIRouter, HTTPException, status
from app.schemas.tools import (
    CalculateRequest,
    CalculateResponse,
    SearchRequest,
    SearchResponse,
    RetrieveRequest,
    RetrieveResponse,
)
from app.services.calculator import safe_calculate
from app.services.search import search_facts
from app.services.retriever import retrieve_documents

router = APIRouter(prefix="/tools", tags=["Tools"])


@router.post("/calculate", response_model=CalculateResponse)
def handle_calculate(req: CalculateRequest):
    """Safely evaluates an arithmetic expression using an AST validator."""
    success, val, err = safe_calculate(req.expression)
    if not success:
        err_lower = (err or "").lower()
        if "division by zero" in err_lower:
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

        raise HTTPException(
            status_code=status_code,
            detail=err,
        )
    return CalculateResponse(
        expression=req.expression,
        result=val,
        error=None,
    )


@router.post("/search", response_model=SearchResponse)
def handle_search(req: SearchRequest):
    """Matches search query keywords against the world facts table."""
    matches = search_facts(req.query)
    return SearchResponse(
        query=req.query,
        matches=matches,
        total_matches=len(matches),
    )


@router.post("/retrieve", response_model=RetrieveResponse)
def handle_retrieve(req: RetrieveRequest):
    """Performs semantic similarity search over Tideline documentation chunks."""
    return retrieve_documents(
        query=req.query,
        top_k=req.top_k or 3,
        source_filter=req.source_filter,
    )
