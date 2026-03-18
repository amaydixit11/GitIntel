import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

# Ensure imports work from project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.gitintel.github import GitHubClient
from src.gitintel.processor import GitProcessor
from src.gitintel.summarizer import Summarizer

load_dotenv()

app = FastAPI(title="GitIntel Local Dev")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use the new optimized 'public' folder
STATIC_DIR = os.path.join(PROJECT_ROOT, "public")

# Serve the main index at root
@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        return f.read()

# Serve API health
@app.get("/api/health")
async def health():
    return {"status": "ok"}

# The main analyzer endpoint
class AnalyzeRequest(BaseModel):
    repo_url: str
    scope: str = "all"
    limit: int = 20
    token: Optional[str] = None

@app.post("/api/analyze")
async def analyze_repo(req: AnalyzeRequest):
    try:
        github = GitHubClient(token=req.token)
        processor = GitProcessor()
        summarizer = Summarizer()

        repo_info = github.parse_repo_url(req.repo_url)
        if not repo_info:
            raise HTTPException(status_code=400, detail="Invalid GitHub repository URL.")
        
        repo_data = await github.fetch_repository_intel(
            owner=repo_info["owner"], 
            name=repo_info["name"], 
            limit=req.limit, 
            scope=req.scope
        )

        full_digest = processor.generate_full_digest(repo_data)
        threads = processor.get_thread_summary_list(repo_data)
        summary = await summarizer.summarize_repo_intel(full_digest)

        return {
            "summary": summary,
            "threads": threads,
            "full_content": full_digest
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Catch-all for slugs (like /facebook/react)
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def catch_all(full_path: str):
    if full_path.startswith("static") or full_path.startswith("api"):
        # Real static files are handled by mount below
        raise HTTPException(status_code=404)
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        return f.read()

# Mount static files at the end
app.mount("/static", StaticFiles(directory=os.path.join(STATIC_DIR, "static")), name="static")

if __name__ == "__main__":
    uvicorn.run("src.server.main:app", host="0.0.0.0", port=8000, reload=True)
