"""
Africa's Talking USSD Service.
"""
import africastalking
from flask import current_app
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class USSDService:
    """Service for handling USSD sessions via Africa's Talking."""

    def __init__(self):
        """Initialize Africa's Talking USSD service."""
        username = current_app.config.get('AT_USERNAME', 'sandbox')
        api_key = current_app.config.get('AT_API_KEY', '')

        if not api_key:
            logger.warning("AT_API_KEY not configured")

        africastalking.initialize(username, api_key)
        self.ussd = africastalking.USSD

    def parse_webhook_data(self, request_data: Dict) -> Dict:
        """
        Parse incoming USSD webhook data from Africa's Talking.

        Args:
            request_data: Request form data or JSON

        Returns:
            Parsed data dictionary
        """
        return {
            'phone_number': request_data.get('phoneNumber', ''),
            'session_id': request_data.get('sessionId', ''),
            'service_code': request_data.get('serviceCode', ''),
            'text': request_data.get('text', '')
        }

    def create_ussd_response(self, message: str, end_session: bool = False) -> str:
        """
        Create USSD response string.

        Args:
            message: Message to display
            end_session: Whether to end the USSD session

        Returns:
            USSD response string
        """
        if end_session:
            return f"END {message}"
        else:
            return f"CON {message}"

    def create_reporting_menu(self) -> str:
        """
        Create USSD menu for reporting scams.

        Returns:
            USSD menu string
        """
        menu = (
            "Welcome to Scam Alert Service\n"
            "1. Report Scam SMS\n"
            "2. Check Blacklist\n"
            "3. Subscribe to Alerts\n"
            "0. Exit"
        )
        return self.create_ussd_response(menu)

    def handle_report_scam(self, phone_number: str, session_id: str) -> str:
        """
        Handle scam reporting via USSD.

        Args:
            phone_number: User's phone number
            session_id: USSD session ID

        Returns:
            USSD response
        """
        message = (
            "Please forward the suspicious SMS to our shortcode.\n"
            "Or type the message content here."
        )
        return self.create_ussd_response(message)

