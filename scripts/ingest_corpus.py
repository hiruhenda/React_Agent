import glob
import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from starlette.testclient import TestClient
from app.main import app


def ingest_all():
    client = TestClient(app)
    corpus_files = sorted(glob.glob(os.path.join(PROJECT_ROOT, "corpus", "*.md")))
    print(f"Found {len(corpus_files)} corpus files to ingest:\n")

    for filepath in corpus_files:
        filename = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            response = client.post(
                "/ingest",
                files={"file": (filename, f, "text/markdown")}
            )
        
        if response.status_code in (200, 201):
            data = response.json()
            chunks = data.get("chunk_count", 0)
            print(f"[OK] Ingested {filename} -> {chunks} chunks")
        else:
            print(f"[ERROR {response.status_code}] Failed {filename}: {response.text}")

    stats_res = client.get("/ingest/stats")
    print("\nCollection Stats:", stats_res.json())


if __name__ == "__main__":
    ingest_all()
