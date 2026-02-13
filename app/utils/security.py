"""
Security utilities for webhook protection.
"""
import hmac
import hashlib
import time
import hashlib as hash_lib
from functools import wraps
from typing import Optional, List
from flask import request, jsonify, current_app
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

# Simple in-memory rate limiter (use Redis in production)
_rate_limit_store = defaultdict(list)

# Replay attack prevention - store seen nonces/timestamps
_seen_nonces = set()
_replay_window_seconds = 300  # 5 minutes


def verify_webhook_signature(signature: str, payload: str, secret: str) -> bool:
    """
    Verify webhook signature using HMAC-SHA256.

    Africa's Talking may send signatures in headers. This verifies:
    - X-Africas-Talking-Signature (if AT uses this)
    - X-Webhook-Signature (generic)
    - Authorization header (Bearer token style)

    Args:
        signature: Signature from request headers
        payload: Request payload (raw body or form data)
        secret: Secret key for verification

    Returns:
        True if signature is valid
    """
    if not signature or not secret:
        return False

    try:
        # Calculate expected signature
        expected = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected)
    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        return False


def verify_webhook_signature_from_request(secret: str) -> bool:
    """
    Verify webhook signature from Flask request.

    Checks multiple header formats:
    - X-Africas-Talking-Signature
    - X-Webhook-Signature
    - Authorization: Bearer <token>

    Args:
        secret: Secret key from config

    Returns:
        True if signature is valid
    """
    if not secret:
        logger.warning("Webhook secret not configured")
        return False

    # Get signature from various possible headers
    signature = (
        request.headers.get('X-Africas-Talking-Signature') or
        request.headers.get('X-Webhook-Signature') or
        request.headers.get('X-Signature')
    )

    # Check Authorization header (Bearer token)
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        signature = signature or auth_header.replace('Bearer ', '')

    if not signature:
        logger.warning("No signature found in request headers")
        return False

    # Get raw payload
    # For form-encoded data (Africa's Talking uses this)
    if request.form:
        # Reconstruct form data as string for signature verification
        payload_parts = []
        for key in sorted(request.form.keys()):
            payload_parts.append(f"{key}={request.form[key]}")
        payload = "&".join(payload_parts)
    elif request.data:
        payload = request.data.decode('utf-8')
    else:
        payload = ""

    return verify_webhook_signature(signature, payload, secret)


def prevent_replay_attack(nonce_field: str = 'id', timestamp_field: str = 'date', max_age_seconds: int = 300):
    """
    Prevent replay attacks by tracking nonces and timestamps.

    Args:
        nonce_field: Field name containing unique request ID
        timestamp_field: Field name containing timestamp
        max_age_seconds: Maximum age of request in seconds

    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get nonce from request
            nonce = None
            if request.form:
                nonce = request.form.get(nonce_field) or request.form.get('linkId')
            elif request.json:
                nonce = request.json.get(nonce_field)

            # Get timestamp
            timestamp_str = None
            if request.form:
                timestamp_str = request.form.get(timestamp_field)
            elif request.json:
                timestamp_str = request.json.get(timestamp_field)

            # Check if nonce already seen
            if nonce:
                nonce_hash = hash_lib.sha256(nonce.encode()).hexdigest()
                if nonce_hash in _seen_nonces:
                    logger.warning(f"Replay attack detected: duplicate nonce {nonce[:10]}...")
                    return jsonify({'error': 'Duplicate request detected'}), 409

                # Add to seen nonces
                _seen_nonces.add(nonce_hash)

                # Clean old nonces (simple cleanup - use Redis in production)
                if len(_seen_nonces) > 10000:
                    _seen_nonces.clear()

            # Check timestamp if provided
            if timestamp_str:
                try:
                    # Parse timestamp (format may vary)
                    from datetime import datetime
                    if 'T' in timestamp_str:
                        # ISO format
                        req_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        # Try common formats
                        req_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

                    age_seconds = (datetime.now() - req_time.replace(tzinfo=None)).total_seconds()

                    if age_seconds > max_age_seconds:
                        logger.warning(f"Request too old: {age_seconds} seconds")
                        return jsonify({'error': 'Request timestamp too old'}), 400

                    if age_seconds < 0:
                        logger.warning(f"Request from future: {age_seconds} seconds")
                        return jsonify({'error': 'Invalid request timestamp'}), 400

                except Exception as e:
                    logger.warning(f"Could not parse timestamp: {e}")
                    # Don't fail on timestamp parsing errors, just log

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def ip_whitelist(allowed_ips: Optional[List[str]] = None):
    """
    IP whitelist decorator for webhook endpoints.

    Args:
        allowed_ips: List of allowed IP addresses/CIDR blocks.
                    If None, uses AT_WEBHOOK_IP_WHITELIST from config.

    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get allowed IPs from config if not provided
            ips_to_check = allowed_ips
            if ips_to_check is None:
                config_ips = current_app.config.get('AT_WEBHOOK_IP_WHITELIST', [])
                if not config_ips:
                    # Default Africa's Talking IP ranges (update with actual IPs)
                    config_ips = [
                        '54.75.249.0/24',  # Example - check AT docs for actual IPs
                        '54.75.250.0/24',
                    ]
                ips_to_check = config_ips

            # If whitelist is disabled, allow all
            if not current_app.config.get('ENABLE_IP_WHITELIST', True):
                return f(*args, **kwargs)

            # Get client IP
            client_ip = request.remote_addr

            # Check X-Forwarded-For header (if behind proxy)
            if request.headers.get('X-Forwarded-For'):
                client_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()

            # Check if IP is in whitelist
            if not _is_ip_allowed(client_ip, ips_to_check):
                logger.warning(f"IP whitelist violation: {client_ip}")
                return jsonify({'error': 'Unauthorized'}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def _is_ip_allowed(ip: str, allowed_ips: list) -> bool:
    """
    Check if IP address is in allowed list (supports CIDR).

    Args:
        ip: IP address to check
        allowed_ips: List of allowed IPs or CIDR blocks

    Returns:
        True if IP is allowed
    """
    import ipaddress

    try:
        ip_obj = ipaddress.ip_address(ip)

        for allowed in allowed_ips:
            if '/' in allowed:
                # CIDR block
                network = ipaddress.ip_network(allowed, strict=False)
                if ip_obj in network:
                    return True
            else:
                # Single IP
                if ip == allowed:
                    return True
    except Exception as e:
        logger.error(f"Error checking IP whitelist: {e}")
        return False

    return False


def rate_limit(max_per_minute: int = 10):
    """
    Rate limiting decorator.

    Args:
        max_per_minute: Maximum requests per minute

    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client identifier (IP or phone number)
            client_id = request.remote_addr
            if 'from' in request.form:
                client_id = request.form.get('from')

            # Clean old entries (older than 1 minute)
            current_time = time.time()
            _rate_limit_store[client_id] = [
                timestamp for timestamp in _rate_limit_store[client_id]
                if current_time - timestamp < 60
            ]

            # Check rate limit
            if len(_rate_limit_store[client_id]) >= max_per_minute:
                return jsonify({
                    'error': 'Rate limit exceeded. Please try again later.'
                }), 429

            # Record this request
            _rate_limit_store[client_id].append(current_time)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_request_data(required_fields: list):
    """
    Validate that required fields are present in request.

    Args:
        required_fields: List of required field names

    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            missing_fields = []
            for field in required_fields:
                if field not in request.form and field not in request.json:
                    missing_fields.append(field)

            if missing_fields:
                return jsonify({
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }), 400

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_webhook_security():
    """
    Combined security decorator for webhooks.
    Applies: signature verification, replay prevention, IP whitelist, rate limiting.

    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get webhook secret from config
            webhook_secret = current_app.config.get('AT_WEBHOOK_SECRET', '')

            # Verify signature if secret is configured
            if webhook_secret and current_app.config.get('ENABLE_WEBHOOK_SIGNATURE', True):
                if not verify_webhook_signature_from_request(webhook_secret):
                    logger.warning("Webhook signature verification failed")
                    return jsonify({'error': 'Invalid signature'}), 401

            # Apply replay prevention
            nonce = request.form.get('id') or request.form.get('linkId') or ''
            if nonce:
                nonce_hash = hash_lib.sha256(nonce.encode()).hexdigest()
                if nonce_hash in _seen_nonces:
                    logger.warning(f"Replay attack detected: {nonce[:10]}...")
                    return jsonify({'error': 'Duplicate request'}), 409
                _seen_nonces.add(nonce_hash)

            # Apply IP whitelist
            if current_app.config.get('ENABLE_IP_WHITELIST', True):
                allowed_ips_list = current_app.config.get('AT_WEBHOOK_IP_WHITELIST', [])
                if allowed_ips_list:
                    client_ip = request.remote_addr
                    if request.headers.get('X-Forwarded-For'):
                        client_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()

                    if not _is_ip_allowed(client_ip, allowed_ips_list):
                        logger.warning(f"IP whitelist violation: {client_ip}")
                        return jsonify({'error': 'Unauthorized'}), 403

            # Apply rate limiting
            client_id = request.remote_addr
            if 'from' in request.form:
                client_id = request.form.get('from')

            current_time = time.time()
            _rate_limit_store[client_id] = [
                ts for ts in _rate_limit_store[client_id]
                if current_time - ts < 60
            ]

            if len(_rate_limit_store[client_id]) >= current_app.config.get('RATE_LIMIT_PER_MINUTE', 10):
                return jsonify({'error': 'Rate limit exceeded'}), 429

            _rate_limit_store[client_id].append(current_time)

            return f(*args, **kwargs)
        return decorated_function
    return decorator
