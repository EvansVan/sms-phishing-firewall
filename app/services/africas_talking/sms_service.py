"""
Africa's Talking SMS Service.
"""
import africastalking
from flask import current_app
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class SMSService:
    """Service for handling SMS via Africa's Talking."""

    def __init__(self):
        """Initialize Africa's Talking SMS service."""
        username = current_app.config.get('AT_USERNAME', 'sandbox')
        api_key = current_app.config.get('AT_API_KEY', '')

        if not api_key:
            logger.warning("AT_API_KEY not configured")

        africastalking.initialize(username, api_key)
        self.sms = africastalking.SMS

    def send_sms(self, message: str, recipients: List[str], sender_id: Optional[str] = None) -> Dict:
        """
        Send SMS message.

        Args:
            message: Message text (max 160 characters for single SMS)
            recipients: List of phone numbers
            sender_id: Optional sender ID (defaults to shortcode)

        Returns:
            Response from Africa's Talking API
        """
        try:
            # Use shortcode if sender_id not provided
            if not sender_id:
                sender_id = current_app.config.get('AT_SHORTCODE')

            # Call Africa's Talking SMS send with correct parameters
            response = self.sms.send(
                message=message,
                recipients=recipients,
                sender_id=sender_id
            )
            logger.info(f"SMS sent to {len(recipients)} recipients: {response}")
            return response
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            raise

    def send_bulk_sms(self, message: str, recipients: List[str], sender_id: Optional[str] = None) -> Dict:
        """
        Send bulk SMS to multiple recipients.

        Args:
            message: Message text
            recipients: List of phone numbers
            sender_id: Optional sender ID

        Returns:
            Response from Africa's Talking API
        """
        # For bulk, we might want to batch the requests
        # Africa's Talking handles batching, but we can optimize here
        return self.send_sms(message, recipients, sender_id)

    def parse_webhook_data(self, request_data: Dict) -> Dict:
        """
        Parse incoming webhook data from Africa's Talking.

        Args:
            request_data: Request form data or JSON

        Returns:
            Parsed data dictionary
        """
        # Africa's Talking sends data as form-encoded
        return {
            'from': request_data.get('from', ''),
            'to': request_data.get('to', ''),
            'text': request_data.get('text', ''),
            'link_id': request_data.get('linkId', ''),
            'date': request_data.get('date', ''),
            'id': request_data.get('id', '')
        }

