import io
import pytest


def test_ingest_valid_markdown(client):
    content = (
        "# Tideline Architecture\n\n"
        "Tideline operates three distinct storage tiers: Raw, Curated, and Archive.\n"
        "The Raw tier retains raw incoming data streams for precisely 14 days before transitioning.\n"
        "Workers poll the ingestion queue at intervals of 500 milliseconds.\n"
    )
    files = {"file": ("architecture.md", io.BytesIO(content.encode("utf-8")), "text/markdown")}
    response = client.post("/ingest", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["source_filename"] == "architecture.md"
    assert data["chunk_count"] >= 1
    assert "collection_stats" in data
    assert data["collection_stats"]["unique_documents"] >= 1


def test_ingest_duplicate_file_reingest(client):
    content = "Tideline tier retention policy updated: Raw tier is 14 days."
    files = {"file": ("policy.txt", io.BytesIO(content.encode("utf-8")), "text/plain")}
    
    # First ingest
    res1 = client.post("/ingest", files=files)
    assert res1.status_code == 201
    
    # Re-ingest same file with overwrite=True
    files2 = {"file": ("policy.txt", io.BytesIO(content.encode("utf-8")), "text/plain")}
    res2 = client.post("/ingest?overwrite=true", files=files2)
    assert res2.status_code == 201
    assert res2.json()["source_filename"] == "policy.txt"


def test_ingest_empty_file_rejected(client):
    files = {"file": ("empty.md", io.BytesIO(b"   \n  "), "text/markdown")}
    response = client.post("/ingest", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_ingest_unsupported_file_extension(client):
    files = {"file": ("binary.pdf", io.BytesIO(b"dummy pdf bytes"), "application/pdf")}
    response = client.post("/ingest", files=files)
    assert response.status_code == 400
    assert "unsupported" in response.json()["detail"].lower()


def test_ingest_stats_endpoint(client):
    response = client.get("/ingest/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_chunks" in data
    assert "unique_documents" in data
    assert data["total_chunks"] >= 0
