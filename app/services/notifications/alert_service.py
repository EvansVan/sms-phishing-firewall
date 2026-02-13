"""
Bulk alert service for campaign notifications.
"""
import logging
from typing import List, Optional
from flask import current_app

from app.services.africas_talking.sms_service import SMSService
from app.services.database.models import DatabaseService
from app.utils.formatters import format_campaign_alert

logger = logging.getLogger(__name__)


class AlertService:
    """Service for sending bulk alerts."""

    def __init__(self):
        """Initialize alert service."""
        self.sms_service = SMSService()
        self.enabled = current_app.config.get('ENABLE_BULK_ALERTS', True)

    def send_campaign_alert(
        self,
        campaign_name: str,
        affected_count: int,
        region: Optional[str] = None
    ) -> dict:
        """
        Send bulk alert about detected campaign.

        Args:
            campaign_name: Name of the campaign
            affected_count: Number of affected users
            region: Optional region filter

        Returns:
            Result dictionary with success status and recipients count
        """
        if not self.enabled:
            logger.info("Bulk alerts disabled")
            return {'success': False, 'reason': 'disabled'}

        try:
            # Get subscribers
            subscribers = DatabaseService.get_subscribers(region=region, active_only=True)

            if not subscribers:
                logger.warning("No subscribers found for campaign alert")
                return {'success': False, 'reason': 'no_subscribers'}

            # Format alert message
            message = format_campaign_alert(campaign_name, affected_count)

            # Get phone numbers
            phone_numbers = [sub.phone_number for sub in subscribers]

            # Send bulk SMS
            response = self.sms_service.send_bulk_sms(message, phone_numbers)

            logger.info(f"Campaign alert sent to {len(phone_numbers)} subscribers")

            return {
                'success': True,
                'recipients': len(phone_numbers),
                'campaign': campaign_name
            }

        except Exception as e:
            logger.error(f"Error sending campaign alert: {e}")
            return {'success': False, 'error': str(e)}

    def send_blacklist_notification(
        self,
        entity_type: str,
        entity_value: str,
        subscribers: Optional[List[str]] = None
    ) -> dict:
        """
        Send notification about new blacklist entry.

        Args:
            entity_type: 'phone' or 'url'
            entity_value: The blocked entity
            subscribers: Optional list of phone numbers (if None, uses all subscribers)

        Returns:
            Result dictionary
        """
        if not self.enabled:
            return {'success': False, 'reason': 'disabled'}

        try:
            from app.utils.formatters import format_blacklist_notification

            if subscribers is None:
                # Get all active subscribers
                db_subscribers = DatabaseService.get_subscribers(active_only=True)
                subscribers = [sub.phone_number for sub in db_subscribers]

            if not subscribers:
                return {'success': False, 'reason': 'no_subscribers'}

            message = format_blacklist_notification(entity_type, entity_value)
            response = self.sms_service.send_bulk_sms(message, subscribers)

            logger.info(f"Blacklist notification sent to {len(subscribers)} subscribers")

            return {
                'success': True,
                'recipients': len(subscribers)
            }

        except Exception as e:
            logger.error(f"Error sending blacklist notification: {e}")
            return {'success': False, 'error': str(e)}

