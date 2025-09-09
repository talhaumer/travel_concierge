from typing import List
import re   
def detect_pii(text: str) -> List[str]:
    """Detect Personally Identifiable Information"""
    pii_patterns = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    }

    detected = []
    for pii_type, pattern in pii_patterns.items():
        if re.search(pattern, text):
            detected.append(pii_type)

    return detected


def redact_pii(text: str) -> str:
    """Redact PII from text"""
    pii_patterns = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    }

    for pattern in pii_patterns.values():
        text = re.sub(pattern, "[REDACTED]", text)

    return text
