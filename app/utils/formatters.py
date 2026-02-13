"""
Message formatting utilities.
"""
from typing import Optional


def format_analysis_response(score: int, summary: str, lesson: Optional[str] = None) -> str:
    """
    Format analysis response for SMS (max 160 characters).

    Args:
        score: Danger score (1-10)
        summary: Short summary
        lesson: Educational tip (optional)

    Returns:
        Formatted message (max 160 chars)
    """
    # Base message
    if score >= 8:
        emoji = "🚨"
        severity = "HIGH RISK"
    elif score >= 5:
        emoji = "⚠️"
        severity = "SUSPICIOUS"
    else:
        emoji = "✅"
        severity = "LOW RISK"

    message = f"{emoji} {severity}: {summary} Score: {score}/10"

    # Add lesson if provided and space allows
    if lesson and len(message) + len(lesson) + 3 <= 160:
        message += f" | {lesson}"
    elif lesson:
        # Truncate lesson if needed
        available = 160 - len(message) - 3
        if available > 10:
            message += f" | {lesson[:available]}"

    # Ensure we don't exceed 160 characters
    return message[:160]


def format_campaign_alert(campaign_name: str, affected_count: int) -> str:
    """
    Format campaign alert message.

    Args:
        campaign_name: Name of the campaign
        affected_count: Number of affected users

    Returns:
        Formatted alert message
    """
    message = f"🚨 SCAM ALERT: {campaign_name} detected. {affected_count}+ reports. Stay safe! #CyberSecurityKenya"
    return message[:160]


def format_blacklist_notification(entity_type: str, entity_value: str) -> str:
    """
    Format blacklist notification message.

    Args:
        entity_type: Type of entity ('phone' or 'url')
        entity_value: The blocked entity

    Returns:
        Formatted notification message
    """
    if entity_type == 'phone':
        message = f"⚠️ Number {entity_value} has been blocked due to scam activity."
    else:
        # Truncate URL if too long
        display_url = entity_value[:50] + "..." if len(entity_value) > 50 else entity_value
        message = f"⚠️ Link {display_url} has been blocked due to scam activity."

    return message[:160]

