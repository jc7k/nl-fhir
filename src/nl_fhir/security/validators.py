"""
Input Validation and Sanitization
HIPAA Compliant: Secure input handling for healthcare data
Medical Safety: Comprehensive validation for clinical text
"""

import re
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def sanitize_clinical_text(text: str) -> str:
    """
    Sanitize clinical text input for security and safety
    Removes potentially harmful characters while preserving medical content

    Args:
        text: Raw clinical text input

    Returns:
        Sanitized clinical text safe for processing
    """
    if not text:
        return text

    # Remove potentially harmful HTML/script content
    text = re.sub(r"<[^>]*>", "", text)

    # Remove script injection patterns and content
    text = re.sub(r"javascript:[^;]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"vbscript:[^;]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"data:[^;]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"alert\s*\([^)]*\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"eval\s*\([^)]*\)", "", text, flags=re.IGNORECASE)

    # Remove control characters except newlines, tabs, and carriage returns
    text = re.sub(r"[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]", "", text)

    # Limit excessive whitespace while preserving medical formatting
    text = re.sub(r"\s{4,}", "   ", text)  # Max 3 consecutive spaces
    text = re.sub(r"\n{4,}", "\n\n\n", text)  # Max 3 consecutive newlines

    # Remove SQL injection patterns
    sql_patterns = [
        r"\b(union|select|insert|update|delete|drop|exec|execute)\s+",
        r"['\";]",
        r"--",
        r"/\*.*?\*/",
    ]

    for pattern in sql_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    return text.strip()


def validate_content_type(content_type: str, allowed_types: Optional[List[str]] = None) -> bool:
    """
    Validate request content type against allowed types

    Args:
        content_type: Request content-type header value
        allowed_types: List of allowed content types

    Returns:
        True if content type is valid, False otherwise
    """
    if not content_type:
        return False

    if allowed_types is None:
        allowed_types = [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
            "text/plain",
        ]

    # Normalize content type (remove charset, boundary, etc.)
    normalized_type = content_type.split(";")[0].strip().lower()

    return any(normalized_type.startswith(allowed_type) for allowed_type in allowed_types)


def validate_request_size(content_length: Optional[str], max_size_bytes: int = 10485760) -> bool:
    """
    Validate request size against maximum allowed size

    Args:
        content_length: Content-Length header value
        max_size_bytes: Maximum allowed request size (default: 10MB)

    Returns:
        True if request size is acceptable, False otherwise
    """
    if not content_length:
        return True  # No content-length header is acceptable

    try:
        size = int(content_length)
        return size <= max_size_bytes
    except (ValueError, TypeError):
        logger.warning(f"Invalid content-length header: {content_length}")
        return False


def validate_patient_reference(patient_ref: str) -> bool:
    """
    Validate patient reference format for FHIR compliance

    Args:
        patient_ref: Patient reference string

    Returns:
        True if valid FHIR patient reference format
    """
    if not patient_ref:
        return False

    # FHIR reference pattern: alphanumeric + dash/underscore/slash
    pattern = r"^[A-Za-z0-9\-_/]+$"
    return bool(re.match(pattern, patient_ref.strip()))


def detect_potential_phi(text: str) -> bool:
    """
    Detect potential PHI patterns in text for logging safety

    Args:
        text: Text to analyze for PHI patterns

    Returns:
        True if potential PHI detected, False otherwise
    """
    if not text:
        return False

    # Common PHI patterns
    phi_patterns = [
        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN pattern
        r"\b\d{10,16}\b",          # Long numbers (insurance, MRN)
        r"\b[A-Z]{1,2}\d{8,12}\b", # Medical record patterns
        r"\b\d{1,2}/\d{1,2}/\d{4}\b", # Date patterns
        r"\b\d{4}-\d{1,2}-\d{1,2}\b", # ISO date patterns
    ]

    for pattern in phi_patterns:
        if re.search(pattern, text):
            return True

    return False