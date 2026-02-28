"""
Input validation utilities.
"""
import re
from typing import Optional, Tuple


def normalize_phone_number(phone: str) -> str:
    """
    Normalize Kenyan phone number to E.164 format (+254XXXXXXXXX).

    Args:
        phone: Raw phone number

    Returns:
        Normalized phone number, or empty string if invalid/empty
    """
    if not phone:
        return ""

    cleaned = re.sub(r'[^\d+]', '', phone.strip())

    if cleaned.startswith('+254') and len(cleaned) == 13:
        return cleaned
    if cleaned.startswith('254') and len(cleaned) == 12:
        return f'+{cleaned}'
    if cleaned.startswith('0') and len(cleaned) == 10:
        return f'+254{cleaned[1:]}'
    if re.fullmatch(r'[17]\d{8}', cleaned):
        return f'+254{cleaned}'

    return ""


def validate_phone_number(phone: str) -> Tuple[bool, Optional[str]]:
    """
    Validate phone number format (Kenyan format).

    Args:
        phone: Phone number string

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not phone:
        return False, "Phone number is required"

    # Remove spaces and special characters
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)

    # Kenyan phone format: +254XXXXXXXXX or 0XXXXXXXXX or 254XXXXXXXXX
    pattern = r'^(\+?254|0)?[17]\d{8}$'

    if not re.match(pattern, cleaned):
        return False, "Invalid phone number format"

    return True, None


def validate_sms_text(text: str, max_length: int = 1000) -> Tuple[bool, Optional[str]]:
    """
    Validate SMS text content.

    Args:
        text: SMS text content
        max_length: Maximum allowed length

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text:
        return False, "SMS text is required"

    if len(text) > max_length:
        return False, f"SMS text exceeds maximum length of {max_length} characters"

    # Check for potentially dangerous content
    dangerous_patterns = [
        r'<script',
        r'javascript:',
        r'onerror=',
        r'onload=',
    ]

    text_lower = text.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, text_lower):
            return False, "SMS contains potentially dangerous content"

    return True, None


def extract_urls(text: str) -> list:
    """
    Extract URLs from text.

    Args:
        text: Text to search for URLs

    Returns:
        List of found URLs
    """
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:!?]'
    urls = re.findall(url_pattern, text)
    return urls


def extract_phone_numbers(text: str) -> list:
    """
    Extract phone numbers from text.

    Args:
        text: Text to search for phone numbers

    Returns:
        List of found phone numbers
    """
    # Pattern for full Kenyan phone numbers (avoid partial capture groups)
    phone_pattern = r'(?<!\d)(?:\+254|254|0)?[17]\d{8}(?!\d)'
    matches = re.findall(phone_pattern, text)

    normalized_phones = []
    for match in matches:
        normalized = normalize_phone_number(match)
        if normalized and normalized not in normalized_phones:
            normalized_phones.append(normalized)

    return normalized_phones


def sanitize_text(text: str) -> str:
    """
    Sanitize text input to prevent injection attacks.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Remove null bytes
    text = text.replace('\x00', '')

    # Remove control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)

    return text.strip()

