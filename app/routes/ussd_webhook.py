"""
USSD webhook routes.
"""
import logging
from flask import Blueprint, request, jsonify
from app.services.africas_talking.ussd_service import USSDService
from app.utils.validators import validate_phone_number

logger = logging.getLogger(__name__)

ussd_bp = Blueprint('ussd', __name__)

# Initialize service
ussd_service = None


def init_service():
    """Initialize USSD service."""
    global ussd_service
    if ussd_service is None:
        ussd_service = USSDService()


@ussd_bp.route('/ussd', methods=['POST'])
def handle_ussd_webhook():
    """
    Handle incoming USSD webhook from Africa's Talking.

    Expected form data:
    - phoneNumber: User's phone number
    - sessionId: USSD session ID
    - serviceCode: Service code
    - text: User input text
    """
    try:
        init_service()

        # Parse webhook data
        webhook_data = ussd_service.parse_webhook_data(request.form)
        phone_number = webhook_data.get('phone_number', '')
        session_id = webhook_data.get('session_id', '')
        text = webhook_data.get('text', '')

        # Validate phone number
        phone_valid, phone_error = validate_phone_number(phone_number)
        if not phone_valid:
            logger.warning(f"Invalid phone number: {phone_error}")
            return ussd_service.create_ussd_response("Invalid phone number", end_session=True)

        # Handle menu navigation
        if not text or text == '':
            # Initial menu
            return ussd_service.create_reporting_menu()

        # Parse user selection
        selections = text.split('*')
        last_selection = selections[-1] if selections else ''

        if last_selection == '1':
            # Report scam
            return ussd_service.handle_report_scam(phone_number, session_id)
        elif last_selection == '2':
            # Check blacklist (placeholder)
            message = "Please forward suspicious SMS to our shortcode for blacklist checking."
            return ussd_service.create_ussd_response(message, end_session=True)
        elif last_selection == '3':
            # Subscribe to alerts
            from app.services.database.models import DatabaseService
            DatabaseService.create_or_update_subscriber(phone_number=phone_number)
            message = "You have been subscribed to scam alerts. Thank you!"
            return ussd_service.create_ussd_response(message, end_session=True)
        elif last_selection == '0':
            # Exit
            return ussd_service.create_ussd_response("Thank you. Stay safe!", end_session=True)
        else:
            # Invalid selection
            message = "Invalid selection. Please try again."
            return ussd_service.create_ussd_response(message, end_session=True)

    except Exception as e:
        logger.error(f"Error handling USSD webhook: {e}", exc_info=True)
        return ussd_service.create_ussd_response(
            "An error occurred. Please try again later.",
            end_session=True
        )

