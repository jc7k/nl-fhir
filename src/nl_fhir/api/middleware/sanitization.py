"""
NL-FHIR Input Sanitization Utilities
HIPAA Compliant: No PHI logging
Medical Safety: Input validation required
"""

import re


def sanitize_clinical_text(text: str) -> str:
    """
    Sanitize clinical text input for security and safety
    Removes potentially harmful characters while preserving medical content
    """
    if not text:
        return text

    # Remove potentially harmful HTML/script content
    text = re.sub(r"<[^>]*>", "", text)

    # Remove control characters except newlines, tabs, and carriage returns
    text = re.sub(r"[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]", "", text)

    # Limit excessive whitespace
    text = re.sub(r"\s{4,}", "   ", text)  # Max 3 consecutive spaces
    text = re.sub(r"\n{4,}", "\n\n\n", text)  # Max 3 consecutive newlines

    return text
