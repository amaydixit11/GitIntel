import httpx
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self._headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        self.url = "https://api.github.com/graphql"

    def parse_repo_url(self, url: str) -> Optional[Dict[str, str]]:
        """Extracts owner and name from a GitHub URL or slug."""
        # Clean URL
        url = url.rstrip("/").replace("https://", "").replace("http://", "").replace("github.com/", "")
        parts = url.split("/")
        
        if len(parts) >= 2:
            return {"owner": parts[0], "name": parts[1]}
        return None

    async def fetch_repository_intel(self, 
        owner: str, 
        name: str, 
        limit: int = 20, 
        scope: str = "all",
        issue_states: Optional[List[str]] = ["OPEN"],
        pr_states: Optional[List[str]] = ["OPEN"]
    ) -> Dict[str, Any]:
        """Fetches issues and PRs using GraphQL with state filtering."""
        
        # Determine query based on scope
        issue_query = ""
        pull_request_query = ""

        if scope in ["all", "issues"]:
            # Default to OPEN if none provided
            istates = issue_states or ["OPEN", "CLOSED"]
            istates_str = f"states: [{', '.join(istates)}]"
            
            issue_query = f"""
            issues(first: {limit}, {istates_str}, orderBy: {{field: CREATED_AT, direction: DESC}}) {{
              nodes {{
                number
                title
                body
                state
                createdAt
                author {{ login }}
                labels(first: 5) {{ nodes {{ name }} }}
                comments(first: 10) {{
                  nodes {{
                    author {{ login }}
                    body
                    createdAt
                  }}
                }}
              }}
            }}
            """

        if scope in ["all", "prs", "decisions"]:
            pstates = pr_states or ["OPEN", "MERGED", "CLOSED"]
            pstates_str = f"states: [{', '.join(pstates)}]"
            
            pull_request_query = f"""
            pullRequests(first: {limit}, {pstates_str}, orderBy: {{field: CREATED_AT, direction: DESC}}) {{
              nodes {{
                number
                title
                body
                state
                createdAt
                author {{ login }}
                labels(first: 5) {{ nodes {{ name }} }}
                comments(first: 10) {{
                  nodes {{
                    author {{ login }}
                    body
                    createdAt
                  }}
                }}
                reviews(first: 10) {{
                  nodes {{
                    state
                    author {{ login }}
                    body
                  }}
                }}
              }}
            }}
            """

        query = f"""
        query {{
          repository(owner: "{owner}", name: "{name}") {{
            name
            owner {{ login }}
            description
            stargazerCount
            forkCount
            {issue_query}
            {pull_request_query}
          }}
        }}
        """

        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {"query": query}
            response = await client.post(self.url, json=payload, headers=self._headers)
            
            if response.status_code != 200:
                raise Exception(f"GitHub API Error: {response.text}")
            
            data = response.json()
            if "errors" in data:
                # Handle common errors like "Not Found" or "Unauthorized"
                error_msg = data["errors"][0]["message"]
                if "Could not resolve to a Repository" in error_msg:
                    raise Exception(f"Repository {owner}/{name} not found.")
                raise Exception(f"GraphQL Error: {error_msg}")
            
            return data["data"]["repository"]
