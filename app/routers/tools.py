from fastapi import APIRouter, HTTPException, status

from app.schemas.tools import (
    SearchRequest,
    SearchResponse,
    RetrieveRequest,
    RetrieveResponse,
    CalculateRequest,
    CalculateResponse,
)
from app.services.calculator import evaluate_expression
from app.services.search import search_facts
from app.services.retriever import retrieve_documents

router = APIRouter(prefix="/tools", tags=["Tools"])


@router.post("/search", response_model=SearchResponse)
def handle_search(req: SearchRequest):
    """Matches search query keywords against the world facts table."""
    matches = search_facts(req.query)
    return SearchResponse(
        query=req.query,
        results=matches,
        total_matches=len(matches),
    )


@router.post("/retrieve", response_model=RetrieveResponse)
def handle_retrieve(req: RetrieveRequest):
    """Performs semantic similarity search over Tideline documentation chunks."""
    chunks = retrieve_documents(
        query=req.query,
        top_k=req.top_k,
        source_filter=req.source_filter,
    )
    return RetrieveResponse(
        query=req.query,
        chunks=chunks,
        total_retrieved=len(chunks),
    )


@router.post("/calculate", response_model=CalculateResponse)
def handle_calculate(req: CalculateRequest):
    """Evaluates arithmetic expressions safely using an AST whitelist."""
    try:
        result = evaluate_expression(req.expression)
        return CalculateResponse(expression=req.expression, result=result)
    except ZeroDivisionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mathematical error: {str(e)}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid expression: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Evaluation failed: {str(e)}",
        )
