from fastapi import APIRouter, UploadFile, File, HTTPException, status, Query
from app.schemas.tools import IngestResponse
from app.services.retriever import ingest_document, get_collection_stats

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post("", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    overwrite: bool = Query(default=True, description="Overwrite existing chunks from this source"),
):
    """
    Ingests text or markdown documentation into ChromaDB with sliding window chunking
    and source metadata tracking.
    """
    filename = file.filename or "uploaded_file.txt"
    if not (filename.endswith(".md") or filename.endswith(".txt")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Please upload .md or .txt files.",
        )

    try:
        raw_bytes = await file.read()
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is not valid UTF-8 text.",
        )

    if not content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty or contains only whitespace.",
        )

    try:
        response = ingest_document(filename=filename, content=content, overwrite=overwrite)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}",
        )


@router.get("/stats")
def collection_statistics():
    """Returns current chunk count and unique document count in ChromaDB."""
    return get_collection_stats()