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

    cleaned = re.sub(r'\D', '', phone.strip())

    # Accept +2547XXXXXXXX / +2541XXXXXXXX (after removing '+')
    if len(cleaned) == 12 and cleaned.startswith('254') and cleaned[3] in {'1', '7'}:
        return f'+{cleaned}'

    # Accept 07XXXXXXXX / 01XXXXXXXX
    if len(cleaned) == 10 and cleaned.startswith('0') and cleaned[1] in {'1', '7'}:
        return f'+254{cleaned[1:]}'

    # Accept 25407XXXXXXXX / 25401XXXXXXXX (common user variant)
    if len(cleaned) == 13 and cleaned.startswith('2540') and cleaned[4] in {'1', '7'}:
        return f'+254{cleaned[4:]}'

    # Accept 7XXXXXXXX / 1XXXXXXXX
    if len(cleaned) == 9 and cleaned[0] in {'1', '7'}:
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

    normalized = normalize_phone_number(phone)
    if not normalized:
        return False, "Invalid phone number format. Use +254XXXXXXXXX, 0XXXXXXXXX, or 254XXXXXXXXX"

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
    # Match common Kenyan number formats in free text
    phone_pattern = r'(?<!\d)(?:\+254[17]\d{8}|254[17]\d{8}|0[17]\d{8}|2540[17]\d{8}|[17]\d{8})(?!\d)'
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

