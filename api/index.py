import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

# Add project root to path so imports work
# Vercel structure: /var/task/api/index.py, root is /var/task
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.gitintel.github import GitHubClient
from src.gitintel.processor import GitProcessor
from src.gitintel.summarizer import Summarizer

load_dotenv()

app = FastAPI(title="GitIntel API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper to serve the frontend
def get_index_html():
    # Try public folder first (Vercel standard)
    path = os.path.join(PROJECT_ROOT, "public", "index.html")
    # Fallback to local frontend/ folder during migration
    if not os.path.exists(path):
        path = os.path.join(PROJECT_ROOT, "frontend", "index.html")
    
    with open(path, "r") as f:
        return f.read()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return get_index_html()

@app.get("/api/health")
async def health():
    return {"status": "ok"}

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

# Catch-all for slugs
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def catch_all(full_path: str):
    # Let static files be served by Vercel CDN if possible
    if full_path.startswith("static/"):
        raise HTTPException(status_code=404)
    # Serve index.html for everything else (slugs)
    return get_index_html()
