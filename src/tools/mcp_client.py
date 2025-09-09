from langchain.tools import BaseTool


class MCPClient(BaseTool):
    def __init__(self, doc_path: str):
        self.doc_path = doc_path

    def run(self, query: str):
        # Simple search for keywords in local docs
        with open(self.doc_path, "r") as f:
            content = f.read()
        if query.lower() in content.lower():
            return f"Found info for '{query}': {content[:200]}..."
        return "No matching info found."
