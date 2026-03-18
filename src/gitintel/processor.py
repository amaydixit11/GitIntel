import re
from typing import Dict, Any, List, Optional
from datetime import datetime

class GitProcessor:
    def __init__(self):
        pass

    def clean_markdown(self, text: str) -> str:
        """Removes excessive whitespace and bot-like patterns."""
        if not text:
            return ""
        # Remove repeated newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Remove common bot footers (simplified)
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        return text.strip()

    def format_thread(self, nodes: List[Dict[str, Any]], item_type: str = "Issue") -> str:
        """Formats a list of issue/PR nodes into a structured text dump."""
        output = []
        for node in nodes:
            number = node.get("number")
            title = node.get("title")
            state = node.get("state")
            author = node.get("author", {}).get("login", "unknown")
            body = self.clean_markdown(node.get("body", ""))
            labels = [l.get("name") for l in node.get("labels", {}).get("nodes", [])]
            
            output.append(f"### {item_type} #{number}: {title}")
            output.append(f"- Status: {state}")
            output.append(f"- Author: @{author}")
            if labels:
                output.append(f"- Labels: {', '.join(labels)}")
            output.append(f"\nDESCRIPTION:\n{body}\n")
            
            # Comments
            comments = node.get("comments", {}).get("nodes", [])
            if comments:
                output.append(f"DISCUSSION THREAD:")
                for comment in comments:
                    c_author = comment.get("author", {}).get("login", "unknown")
                    c_body = self.clean_markdown(comment.get("body", ""))
                    if len(c_body) > 1000:
                        c_body = c_body[:1000] + "... (truncated)"
                    output.append(f"  [@{c_author}]: {c_body}")
                output.append("\n" + "-"*40 + "\n")
            else:
                output.append("-" * 40 + "\n")
        
        return "\n".join(output)

    def generate_full_digest(self, repo_data: Dict[str, Any]) -> str:
        """Generates the full LLM-ready text content for the whole repository."""
        name = repo_data.get("name")
        owner = repo_data.get("owner", {}).get("login")
        desc = repo_data.get("description", "No description provided.")
        
        digest = [
            f"============================================================",
            f"REPOSITORY: {owner}/{name}",
            f"DESCRIPTION: {desc}",
            f"GENERATED ON: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"============================================================",
            "\n"
        ]

        # Issues
        if "issues" in repo_data:
            digest.append("## ISSUES\n")
            digest.append(self.format_thread(repo_data["issues"].get("nodes", []), "Issue"))
            digest.append("\n" + "="*60 + "\n")

        # Pull Requests
        if "pullRequests" in repo_data:
            digest.append("## PULL REQUESTS\n")
            digest.append(self.format_thread(repo_data["pullRequests"].get("nodes", []), "PR"))
            digest.append("\n" + "="*60 + "\n")

        return "\n".join(digest)

    def get_thread_summary_list(self, repo_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extracts a lightweight list of threads for the UI."""
        threads = []
        if "issues" in repo_data:
            for n in repo_data["issues"].get("nodes", []):
                threads.append({
                    "id": n.get("number"),
                    "title": n.get("title"),
                    "type": "Issue",
                    "status": n.get("state")
                })
        
        if "pullRequests" in repo_data:
            for n in repo_data["pullRequests"].get("nodes", []):
                threads.append({
                    "id": n.get("number"),
                    "title": n.get("title"),
                    "type": "PR",
                    "status": n.get("state")
                })
        
        # Sort by ID descending
        threads.sort(key=lambda x: x["id"], reverse=True)
        return threads
