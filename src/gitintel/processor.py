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
                    co_author = comment.get("author", {}).get("login", "unknown") if comment.get("author") else "unknown"
                    c_body = self.clean_markdown(comment.get("body", ""))
                    if len(c_body) > 1000:
                        c_body = c_body[:1000] + "... (truncated)"
                    output.append(f"  [@{co_author}]: {c_body}")
                output.append("\n" + "-"*40 + "\n")
            else:
                output.append("-" * 40 + "\n")
        
        return "\n".join(output)

    def generate_full_digest(self, repo_data: Dict[str, Any], search: str = None, search_in: list = None, labels: list = None) -> str:
        """Generates the full LLM-ready text content for the whole repository."""
        repo_data = repo_data or {}
        search_in = search_in or ["title", "body", "comments"]
        
        name = repo_data.get("name", "Unknown")
        owner = repo_data.get("owner", {}).get("login", "Unknown") if repo_data.get("owner") else "Unknown"
        desc = repo_data.get("description", "No description provided.")
        
        digest = [
            f"============================================================",
            f"REPOSITORY: {owner}/{name}",
            f"DESCRIPTION: {desc}",
            f"GENERATED ON: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"============================================================",
            "\n"
        ]

        def filter_nodes(nodes):
            return [n for n in nodes if n and self._matches_filters(n, search, search_in, labels)]

        # Issues
        issues_node = repo_data.get("issues")
        if issues_node:
            filtered = filter_nodes(issues_node.get("nodes", []))
            if filtered:
                digest.append("## ISSUES\n")
                digest.append(self.format_thread(filtered, "Issue"))
                digest.append("\n" + "="*60 + "\n")

        # Pull Requests
        prs_node = repo_data.get("pullRequests")
        if prs_node:
            filtered = filter_nodes(prs_node.get("nodes", []))
            if filtered:
                digest.append("## PULL REQUESTS\n")
                digest.append(self.format_thread(filtered, "PR"))
                digest.append("\n" + "="*60 + "\n")

        return "\n".join(digest)

    def get_thread_summary_list(self, repo_data: Dict[str, Any], search: str = None, search_in: list = None, labels: list = None) -> List[Dict[str, Any]]:
        """Extracts a lightweight list of threads for the UI."""
        threads = []
        repo_data = repo_data or {}
        search_in = search_in or ["title", "body", "comments"]
        
        sections = [("issues", "Issue"), ("pullRequests", "PR")]
        
        for key, label in sections:
            node_root = repo_data.get(key)
            if node_root:
                for n in node_root.get("nodes", []):
                    if not n: continue
                    if self._matches_filters(n, search, search_in, labels):
                        threads.append({
                            "id": n.get("number"),
                            "title": n.get("title"),
                            "type": label,
                            "status": n.get("state")
                        })
        
        # Sort by ID descending
        threads.sort(key=lambda x: x.get("id", 0) or 0, reverse=True)
        return threads

    def get_knowledge_graph(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Builds a network graph of connections between issues and PRs."""
        nodes = []
        links = []
        node_map = {} # number -> node_index

        all_nodes = []
        if repo_data.get("issues"):
            all_nodes.extend([(n, "Issue") for n in repo_data["issues"].get("nodes", []) if n])
        if repo_data.get("pullRequests"):
            all_nodes.extend([(n, "PR") for n in repo_data["pullRequests"].get("nodes", []) if n])

        # 1. Create Nodes
        for i, (node, ntype) in enumerate(all_nodes):
            num = node.get("number")
            nodes.append({
                "id": str(num),
                "title": node.get("title"),
                "type": ntype,
                "state": node.get("state")
            })
            node_map[num] = i

        # 2. Find Mentions (Links)
        mention_regex = re.compile(r'#(\d+)')
        
        for i, (node, ntype) in enumerate(all_nodes):
            current_num = node.get("number")
            
            # Text to scan: Body + Comments
            text_to_scan = node.get("body", "") or ""
            comments = node.get("comments", {}).get("nodes", [])
            for c in comments:
                text_to_scan += " " + (c.get("body", "") or "")
            
            mentions = set(mention_regex.findall(text_to_scan))
            for m in mentions:
                target_num = int(m)
                if target_num in node_map and target_num != current_num:
                    links.append({
                        "source": str(current_num),
                        "target": str(target_num)
                    })

        return {"nodes": nodes, "links": links}

    def _matches_filters(self, node: Dict[str, Any], search: str, search_in: list, labels: list) -> bool:
        """Helper to check if a node matches the provided search criteria."""
        if not search and not labels:
            return True
            
        # 1. Label Filter
        if labels:
            node_labels = [l.get("name").lower() for l in node.get("labels", {}).get("nodes", [])]
            if not any(lab.lower() in node_labels for lab in labels):
                return False
        
        # 2. Search Term
        if search:
            search_str = search.lower()
            match_found = False
            
            if "title" in search_in and search_str in node.get("title", "").lower():
                match_found = True
            elif "body" in search_in and search_str in node.get("body", "").lower():
                match_found = True
            elif "comments" in search_in:
                comments = node.get("comments", {}).get("nodes", [])
                for c in comments:
                    if search_str in c.get("body", "").lower():
                        match_found = True
                        break
            
            if not match_found:
                return False
                
        return True
