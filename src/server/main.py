import os
import sys

# Add project root to path so imports work
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from dotenv import load_dotenv

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

# Static files
# Ensure the directories exist
os.makedirs("frontend/static/css", exist_ok=True)
os.makedirs("frontend/static/js", exist_ok=True)
os.makedirs("frontend/static/icons", exist_ok=True)

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

class AnalyzeRequest(BaseModel):
    repo_url: str
    scope: str = "all"
    limit: int = 20
    token: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("frontend/index.html") as f:
        return f.read()

# Imports moved to top of file

@app.post("/api/analyze")
async def analyze_repo(req: AnalyzeRequest):
    """
    Analyzes a GitHub repository's issues and PRs.
    """
    try:
        # 1. Initialize tools
        github = GitHubClient(token=req.token)
        processor = GitProcessor()
        summarizer = Summarizer()

        # 2. Parse repo URL
        repo_info = github.parse_repo_url(req.repo_url)
        if not repo_info:
            raise HTTPException(status_code=400, detail="Invalid GitHub repository URL.")
        
        # 3. Fetch data using GraphQL
        repo_data = await github.fetch_repository_intel(
            owner=repo_info["owner"], 
            name=repo_info["name"], 
            limit=req.limit, 
            scope=req.scope
        )

        # 4. Process data into full digest
        full_digest = processor.generate_full_digest(repo_data)
        
        # 5. Extract thread list for UI
        threads = processor.get_thread_summary_list(repo_data)
        
        # 6. Generate AI intelligence summary
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

if __name__ == "__main__":
    uvicorn.run("src.server.main:app", host="0.0.0.0", port=8000, reload=True)
