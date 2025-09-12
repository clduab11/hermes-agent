"""Input validation and sanitisation helpers for OWASP compliance."""
from __future__ import annotations

import html
import re
import urllib.parse
from typing import Any, Dict, List, Optional

__all__ = ["sanitize_text", "validate_email", "sanitize_html", "prevent_sql_injection", "validate_legal_content"]

# Regex patterns for security validation
_SCRIPT_RE = re.compile(r"<\/?script.*?>", re.IGNORECASE)
_SQL_INJECTION_RE = re.compile(
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|EXEC|EXECUTE|DECLARE)\b)"
    r"|('(\s*|\d+\s*|\w+\s*)')|(\-\-)|(/\*.*\*/)|(\bOR\b\s*\d+\s*=\s*\d+)"
    r"|(\bAND\b\s*\d+\s*=\s*\d+)|(\|\|)|(\+\+)", 
    re.IGNORECASE
)
_XSS_PATTERNS = [
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"vbscript:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"<\s*iframe", re.IGNORECASE),
    re.compile(r"<\s*object", re.IGNORECASE),
    re.compile(r"<\s*embed", re.IGNORECASE),
    re.compile(r"<\s*link", re.IGNORECASE),
    re.compile(r"<\s*meta", re.IGNORECASE),
]
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# Legal-specific content validation patterns
_PROHIBITED_LEGAL_ADVICE_PATTERNS = [
    re.compile(r"\byou should (sue|file|litigate|divorce)\b", re.IGNORECASE),
    re.compile(r"\bI recommend you (sue|file|litigate|divorce)\b", re.IGNORECASE),
    re.compile(r"\byou have grounds for\b", re.IGNORECASE),
    re.compile(r"\byou will win\b", re.IGNORECASE),
    re.compile(r"\bguaranteed success\b", re.IGNORECASE),
]

_PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN
    re.compile(r"\b\d{4}-\d{4}-\d{4}-\d{4}\b"),  # Credit card
    re.compile(r"\b[A-Z]{1,2}\d{6,8}[A-Z]?\b"),  # Driver's license
]


def sanitize_text(value: str) -> str:
    """Enhanced HTML/JS sanitizer for defensive programming.

    Provides protection against XSS attacks while preserving content integrity.
    """
    if not value:
        return ""

    # Remove script tags
    cleaned = _SCRIPT_RE.sub("", value)
    
    # Remove XSS patterns
    for pattern in _XSS_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    
    # HTML encode remaining content
    cleaned = html.escape(cleaned, quote=True)
    
    # Normalize whitespace
    return re.sub(r"\s+", " ", cleaned).strip()


def sanitize_html(value: str, allowed_tags: Optional[List[str]] = None) -> str:
    """Sanitize HTML content allowing only specified tags.
    
    Args:
        value: HTML content to sanitize
        allowed_tags: List of allowed HTML tags (default: safe subset)
    """
    if not value:
        return ""
    
    if allowed_tags is None:
        allowed_tags = ["p", "br", "strong", "em", "ul", "ol", "li", "a", "h1", "h2", "h3"]
    
    # Remove script tags and dangerous content
    cleaned = _SCRIPT_RE.sub("", value)
    
    for pattern in _XSS_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    
    # Simple tag filtering (for production use a proper library like bleach)
    allowed_pattern = "|".join(allowed_tags)
    tag_pattern = re.compile(f"<(?!/?({allowed_pattern})\\b)[^>]*>", re.IGNORECASE)
    cleaned = tag_pattern.sub("", cleaned)
    
    return cleaned.strip()


def validate_email(email: str) -> bool:
    """Validate email address format."""
    if not email or len(email) > 254:
        return False
    return bool(_EMAIL_RE.match(email))


def prevent_sql_injection(value: str) -> str:
    """Detect and prevent SQL injection attempts.
    
    Raises ValueError if potential SQL injection is detected.
    """
    if not value:
        return value
        
    if _SQL_INJECTION_RE.search(value):
        raise ValueError("Potential SQL injection detected")
        
    return value


def validate_legal_content(content: str) -> Dict[str, Any]:
    """Validate legal content for compliance and safety.
    
    Returns:
        Dict with validation results and warnings
    """
    result = {
        "is_valid": True,
        "warnings": [],
        "pii_detected": [],
        "prohibited_advice": []
    }
    
    if not content:
        return result
    
    # Check for prohibited legal advice patterns
    for pattern in _PROHIBITED_LEGAL_ADVICE_PATTERNS:
        matches = pattern.findall(content)
        if matches:
            result["prohibited_advice"].extend(matches)
            result["warnings"].append("Content may contain specific legal advice")
    
    # Check for PII patterns
    for i, pattern in enumerate(_PII_PATTERNS):
        matches = pattern.findall(content)
        if matches:
            pii_type = ["SSN", "Credit Card", "Driver's License"][i]
            result["pii_detected"].append({"type": pii_type, "matches": len(matches)})
            result["warnings"].append(f"Potential {pii_type} detected")
    
    # Mark as invalid if critical issues found
    if result["prohibited_advice"] or result["pii_detected"]:
        result["is_valid"] = False
    
    return result


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations."""
    if not filename:
        return "untitled"
    
    # Remove directory traversal attempts
    cleaned = filename.replace("../", "").replace("..\\", "")
    
    # Remove dangerous characters
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", cleaned)
    
    # Limit length
    cleaned = cleaned[:255]
    
    return cleaned.strip() or "untitled"


def validate_url(url: str, allowed_schemes: Optional[List[str]] = None) -> bool:
    """Validate URL format and scheme."""
    if not url:
        return False
        
    if allowed_schemes is None:
        allowed_schemes = ["http", "https"]
    
    try:
        parsed = urllib.parse.urlparse(url)
        return (
            parsed.scheme in allowed_schemes and
            bool(parsed.netloc) and
            not any(dangerous in url.lower() for dangerous in ["javascript:", "data:", "vbscript:"])
        )
    except Exception:
        return False


def sanitize_json_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively sanitize all string values in a JSON object."""
    if isinstance(data, dict):
        return {key: sanitize_json_values(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_json_values(item) for item in data]
    elif isinstance(data, str):
        return sanitize_text(data)
    else:
        return data
