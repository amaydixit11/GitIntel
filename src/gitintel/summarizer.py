import os
from openai import OpenAI
from typing import Dict, Any, List, Optional

class Summarizer:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    async def summarize_repo_intel(self, full_digest: str) -> str:
        """Uses an LLM to extract high-level intelligence from the repo digest."""
        if not self.client:
            return "No OpenAI API key found. Please provide one for AI-powered intelligence summaries."

        # Truncate if too long (simple version)
        if len(full_digest) > 100000:
            full_digest = full_digest[:100000] + "... (truncated for context limits)"

        prompt = f"""
        You are an expert software architect analyzing a repository's current state from its issues and pull requests.
        Below is a structured digest of recent activities.
        
        Analyze this and provide:
        1.  **Core Architecture & Status**: What are the main technical goals right now?
        2.  **Key Decisions**: What important decisions have maintainers made recently?
        3.  **Hidden Constraints**: Are there legacy issues or constraints mentioned in the PR discussions?
        4.  **Contributor Entry Points**: Which issues look most approachable or critical for new contributors?

        Digest:
        {full_digest}

        Please present the summary in a clean, professional tone with bullet points.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a senior software engineering assistant specializing in repository analysis and context extraction."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating summary: {str(e)}"
