"""
Configuration management for SMS Phishing Firewall
"""
import os
from pathlib import Path

# Base directory
basedir = Path(__file__).parent.parent


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Flask creates instance/ dir by default; use that for SQLite
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///instance/firewall.db'
    )

    # Africa's Talking
    AT_USERNAME = os.getenv('AT_USERNAME', 'sandbox')
    AT_API_KEY = os.getenv('AT_API_KEY', '')
    AT_SHORTCODE = os.getenv('AT_SHORTCODE')

    # Google Gemini / Vertex AI
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
    GEMINI_MODEL_CANDIDATES = os.getenv('GEMINI_MODEL_CANDIDATES', '')
    USE_VERTEX_AI = os.getenv('USE_VERTEX_AI', 'false').lower() == 'true'

    # Vertex AI specific (if using GCP)
    GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID', '')
    GCP_LOCATION = os.getenv('GCP_LOCATION', 'us-central1')

    # Feature flags
    ENABLE_BLACKLIST = os.getenv('ENABLE_BLACKLIST', 'true').lower() == 'true'
    ENABLE_CAMPAIGN_DETECTION = os.getenv('ENABLE_CAMPAIGN_DETECTION', 'true').lower() == 'true'
    ENABLE_BULK_ALERTS = os.getenv('ENABLE_BULK_ALERTS', 'true').lower() == 'true'
    ENABLE_SOCIAL_MEDIA = os.getenv('ENABLE_SOCIAL_MEDIA', 'false').lower() == 'true'

    # Blacklist thresholds
    BLACKLIST_SCORE_THRESHOLD = int(os.getenv('BLACKLIST_SCORE_THRESHOLD', '8'))
    URL_BLACKLIST_SCORE_THRESHOLD = int(os.getenv('URL_BLACKLIST_SCORE_THRESHOLD', '9'))
    CAMPAIGN_DETECTION_THRESHOLD = int(os.getenv('CAMPAIGN_DETECTION_THRESHOLD', '5'))

    # Social Media (optional)
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY', '')
    TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET', '')
    TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN', '')
    TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET', '')

    # Security
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '10'))

    # Webhook Security
    AT_WEBHOOK_SECRET = os.getenv('AT_WEBHOOK_SECRET', '')
    ENABLE_WEBHOOK_SIGNATURE = os.getenv('ENABLE_WEBHOOK_SIGNATURE', 'true').lower() == 'true'
    ENABLE_IP_WHITELIST = os.getenv('ENABLE_IP_WHITELIST', 'true').lower() == 'true'
    ENABLE_REPLAY_PROTECTION = os.getenv('ENABLE_REPLAY_PROTECTION', 'true').lower() == 'true'

    # IP Whitelist (comma-separated or JSON array)
    # Get from: https://help.africastalking.com or contact AT support
    AT_WEBHOOK_IP_WHITELIST = os.getenv('AT_WEBHOOK_IP_WHITELIST', '').split(',') if os.getenv('AT_WEBHOOK_IP_WHITELIST') else []
    # Remove empty strings
    AT_WEBHOOK_IP_WHITELIST = [ip.strip() for ip in AT_WEBHOOK_IP_WHITELIST if ip.strip()]

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    # Use PostgreSQL in production
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://user:pass@localhost/firewall'
    )


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

