"""
Community blacklist management.
"""
from typing import Optional
from flask import current_app
from app.services.database.models import DatabaseService
import logging

logger = logging.getLogger(__name__)


class BlacklistService:
    """Service for blacklist management."""

    @staticmethod
    def check_and_add_to_blacklist(
        score: int,
        phone_number: Optional[str] = None,
        url: Optional[str] = None
    ) -> tuple:
        """
        Check score thresholds and add to blacklist if needed.

        Args:
            score: Danger score from analysis
            phone_number: Phone number to potentially blacklist
            url: URL to potentially blacklist

        Returns:
            Tuple of (phone_blacklisted, url_blacklisted)
        """
        phone_blacklisted = False
        url_blacklisted = False

        # Check phone blacklist threshold
        if phone_number and score >= current_app.config.get('BLACKLIST_SCORE_THRESHOLD', 8):
            try:
                DatabaseService.add_to_blacklist(
                    entity_type='phone',
                    entity_value=phone_number,
                    auto_blocked=True,
                    reason=f'Auto-blocked due to high danger score: {score}/10'
                )
                phone_blacklisted = True
                logger.info(f"Auto-blacklisted phone: {phone_number} (score: {score})")
            except Exception as e:
                logger.error(f"Error blacklisting phone {phone_number}: {e}")

        # Check URL blacklist threshold
        if url and score >= current_app.config.get('URL_BLACKLIST_SCORE_THRESHOLD', 9):
            try:
                DatabaseService.add_to_blacklist(
                    entity_type='url',
                    entity_value=url,
                    auto_blocked=True,
                    reason=f'Auto-blocked due to high danger score: {score}/10'
                )
                url_blacklisted = True
                logger.info(f"Auto-blacklisted URL: {url} (score: {score})")
            except Exception as e:
                logger.error(f"Error blacklisting URL {url}: {e}")

        return phone_blacklisted, url_blacklisted

    @staticmethod
    def is_entity_blacklisted(phone_number: Optional[str] = None, url: Optional[str] = None) -> bool:
        """
        Check if phone or URL is blacklisted.

        Args:
            phone_number: Phone number to check
            url: URL to check

        Returns:
            True if any entity is blacklisted
        """
        if phone_number and DatabaseService.is_blacklisted('phone', phone_number):
            return True
        if url and DatabaseService.is_blacklisted('url', url):
            return True
        return False

