import os
from openai import OpenAI
from typing import Dict, Any, List, Optional

class Summarizer:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    async def summarize_repo_intel(self, full_digest: str) -> str:
        """Uses an LLM to extract high-level intelligence or falls back to rules."""
        # Fallback if no key or key is a placeholder
        if not self.client or "your_openai_api_key" in (self.api_key or ""):
            return self._generate_rule_based_summary(full_digest)

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
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a senior software engineering assistant specializing in repository analysis and context extraction."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            # Fallback on credential errors
            if "401" in str(e) or "Incorrect API key" in str(e):
                return self._generate_rule_based_summary(full_digest)
            return f"Error generating summary: {str(e)}"

    def _generate_rule_based_summary(self, full_digest: str) -> str:
        """Fallback when no LLM key is available."""
        # Simple extraction of counts
        issues_count = full_digest.count("### Issue #")
        prs_count = full_digest.count("### PR #")
        
        # Simple extraction of the first few titles
        lines = full_digest.split("\n")
        recent_items = []
        for line in lines:
            if line.startswith("### Issue #") or line.startswith("### PR #"):
                recent_items.append(line.replace("### ", "").strip())
                if len(recent_items) >= 5:
                    break

        recent_items_str = "\n".join([f"- {item}" for item in recent_items]) if recent_items else "- No recent items found."

        return f"""
📢 **GitIntel Rule-Based Analysis (AI disabled)**
Total activity captured: {issues_count} Issues and {prs_count} PRs.

**Recently Analyzed Threads:**
{recent_items_str}

*Note: OpenAI key is missing or invalid. Provide a real one to unlock deep structural analysis, architectural decisions, and constraints identifying.*
        """
