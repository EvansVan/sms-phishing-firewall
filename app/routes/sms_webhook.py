"""
SMS webhook routes.
"""
import logging
from flask import Blueprint, request, jsonify, current_app
from app.services.africas_talking.sms_service import SMSService
from app.services.gemini.analyzer import GeminiAnalyzer
from app.services.database.models import DatabaseService
from app.services.database.blacklist import BlacklistService
from app.services.notifications.alert_service import AlertService
from app.services.notifications.social_media import SocialMediaService
from app.utils.validators import (
    validate_phone_number,
    validate_sms_text,
    extract_urls,
    extract_phone_numbers,
    normalize_phone_number,
    sanitize_text
)
from app.utils.formatters import format_analysis_response
from app.utils.security import (
    rate_limit,
    validate_request_data,
    require_webhook_security,
    verify_webhook_signature_from_request,
    prevent_replay_attack,
    ip_whitelist
)

logger = logging.getLogger(__name__)

sms_bp = Blueprint('sms', __name__)

# Initialize services
sms_service = None
gemini_analyzer = None
alert_service = None
social_media_service = None


def init_services():
    """Initialize services (called after app context is available)."""
    global sms_service, gemini_analyzer, alert_service, social_media_service
    if sms_service is None:
        sms_service = SMSService()
    if gemini_analyzer is None:
        gemini_analyzer = GeminiAnalyzer()
    if alert_service is None:
        alert_service = AlertService()
    if social_media_service is None:
        social_media_service = SocialMediaService()
    return sms_service, gemini_analyzer, alert_service, social_media_service


@sms_bp.route('/sms', methods=['POST'])
@validate_request_data(['from', 'text'])
def handle_sms_webhook():
    """
    Handle incoming SMS webhook from Africa's Talking.

    Expected form data:
    - from: Sender phone number
    - text: Message text
    - to: Recipient (shortcode)
    - linkId: Link ID for response
    """
    try:
        # Security checks
        webhook_secret = current_app.config.get('AT_WEBHOOK_SECRET', '')

        # Verify signature if enabled and secret is configured
        if webhook_secret and current_app.config.get('ENABLE_WEBHOOK_SIGNATURE', True):
            if not verify_webhook_signature_from_request(webhook_secret):
                logger.warning("Webhook signature verification failed")
                return jsonify({'error': 'Invalid signature'}), 401

        # Check IP whitelist if enabled
        if current_app.config.get('ENABLE_IP_WHITELIST', True):
            allowed_ips = current_app.config.get('AT_WEBHOOK_IP_WHITELIST', [])
            if allowed_ips:
                from app.utils.security import _is_ip_allowed
                client_ip = request.remote_addr
                if request.headers.get('X-Forwarded-For'):
                    client_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()

                if not _is_ip_allowed(client_ip, allowed_ips):
                    logger.warning(f"IP whitelist violation: {client_ip}")
                    return jsonify({'error': 'Unauthorized IP'}), 403

        # Replay attack prevention
        if current_app.config.get('ENABLE_REPLAY_PROTECTION', True):
            request_id = request.form.get('id') or request.form.get('linkId', '')
            if request_id:
                import hashlib
                from app.utils.security import _seen_nonces
                nonce_hash = hashlib.sha256(request_id.encode()).hexdigest()
                if nonce_hash in _seen_nonces:
                    logger.warning(f"Replay attack detected: {request_id[:10]}...")
                    return jsonify({'error': 'Duplicate request detected'}), 409
                _seen_nonces.add(nonce_hash)

        (
            local_sms_service,
            local_gemini_analyzer,
            local_alert_service,
            local_social_media_service
        ) = init_services()

        # Parse webhook data
        webhook_data = local_sms_service.parse_webhook_data(request.form)
        reporter_phone = webhook_data.get('from', '')
        message_text = webhook_data.get('text', '')

        # Validate input
        phone_valid, phone_error = validate_phone_number(reporter_phone)
        if not phone_valid:
            logger.warning(f"Invalid phone number: {phone_error}")
            return jsonify({'error': phone_error}), 400

        text_valid, text_error = validate_sms_text(message_text)
        if not text_valid:
            logger.warning(f"Invalid SMS text: {text_error}")
            return jsonify({'error': text_error}), 400

        # Sanitize input
        message_text = sanitize_text(message_text)

        # Extract URLs and phone numbers
        detected_urls = extract_urls(message_text)
        detected_phones = extract_phone_numbers(message_text)
        normalized_reporter_phone = normalize_phone_number(reporter_phone)

        # Check blacklist first
        original_sender = next(
            (phone for phone in detected_phones if phone != normalized_reporter_phone),
            None
        )

        if not original_sender:
            response_msg = (
                "⚠️ Please include the sender phone number in the SMS you report "
                "(e.g., 'From: +2547XXXXXXXX ...' or 'From: 07XXXXXXXX' or 'From: 2547XXXXXXXX') "
                "so we can trace and blacklist the scammer."
            )
            local_sms_service.send_sms(response_msg, [reporter_phone])
            return jsonify({
                'status': 'ok',
                'action': 'missing_sender_phone'
            }), 200

        if original_sender and BlacklistService.is_entity_blacklisted(phone_number=original_sender):
            response_msg = "⚠️ This sender is already blacklisted. Thank you for reporting!"
            local_sms_service.send_sms(response_msg, [reporter_phone])
            return jsonify({'status': 'ok', 'action': 'blacklisted'}), 200

        if detected_urls:
            for url in detected_urls:
                if BlacklistService.is_entity_blacklisted(url=url):
                    response_msg = "⚠️ This link is already blacklisted. Thank you for reporting!"
                    local_sms_service.send_sms(response_msg, [reporter_phone])
                    return jsonify({'status': 'ok', 'action': 'blacklisted'}), 200

        # Analyze with Gemini
        logger.info(f"Analyzing message from {reporter_phone}")
        analysis = local_gemini_analyzer.analyze_message(
            message_text=message_text,
            sender=original_sender,
            urls=detected_urls,
            phones=detected_phones
        )

        score = analysis.get('score', 5)
        summary = analysis.get('summary', 'Message analyzed')
        lesson = analysis.get('lesson', 'Stay safe!')
        is_campaign = analysis.get('is_campaign', False)

        # Save to database
        scam_log = DatabaseService.save_scam_log(
            reporter_phone=reporter_phone,
            message_text=message_text,
            score=score,
            original_sender=original_sender,
            analysis_json=analysis,
            detected_urls=detected_urls,
            is_campaign=is_campaign
        )

        # Check and add to blacklist if threshold met
        phone_blacklisted, url_blacklisted = BlacklistService.check_and_add_to_blacklist(
            score=score,
            phone_number=original_sender,
            url=detected_urls[0] if detected_urls else None
        )

        # Format and send response
        response_msg = format_analysis_response(score, summary, lesson)
        local_sms_service.send_sms(response_msg, [reporter_phone])

        # Post to social media if high danger
        if score >= 8 and current_app.config.get('ENABLE_SOCIAL_MEDIA', False):
            local_social_media_service.post_campaign_alert(
                scam_text=message_text,
                lesson=lesson,
                score=score
            )

        logger.info(f"SMS processed: Score={score}, Campaign={is_campaign}, Blacklisted={phone_blacklisted or url_blacklisted}")

        return jsonify({
            'status': 'ok',
            'score': score,
            'is_campaign': is_campaign,
            'blacklisted': phone_blacklisted or url_blacklisted
        }), 200

    except Exception as e:
        logger.error(f"Error handling SMS webhook: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

