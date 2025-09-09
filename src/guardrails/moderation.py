from typing import Dict, Any
# moderation.py
def moderate_content(content: str) -> Dict[str, Any]:
    """Basic content moderation"""
    blacklist = ["illegal", "dangerous", "unsafe", "exploit"]
    issues = []

    for word in blacklist:
        if word in content.lower():
            issues.append(f"Contains blacklisted word: {word}")

    return {"is_safe": len(issues) == 0, "issues": issues}
