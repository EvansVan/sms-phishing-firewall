"""
SQLAlchemy models for SMS Phishing Firewall
"""
from datetime import datetime
from app import db
import json


class ScamLog(db.Model):
    """Log of reported scam messages."""
    __tablename__ = 'scam_logs'

    id = db.Column(db.Integer, primary_key=True)
    reporter_phone = db.Column(db.String(20), nullable=False, index=True)
    original_sender = db.Column(db.String(20), nullable=True, index=True)
    message_text = db.Column(db.Text, nullable=False)
    score = db.Column(db.Integer, nullable=False, index=True)
    analysis_json = db.Column(db.Text, nullable=True)  # Store full Gemini response
    detected_urls = db.Column(db.Text, nullable=True)  # JSON array of URLs
    is_campaign = db.Column(db.Boolean, default=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'reporter_phone': self.reporter_phone,
            'original_sender': self.original_sender,
            'message_text': self.message_text,
            'score': self.score,
            'analysis': json.loads(self.analysis_json) if self.analysis_json else None,
            'detected_urls': json.loads(self.detected_urls) if self.detected_urls else [],
            'is_campaign': self.is_campaign,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class Blacklist(db.Model):
    """Community blacklist of phone numbers and URLs."""
    __tablename__ = 'blacklist'

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(10), nullable=False, index=True)  # 'phone' or 'url'
    entity_value = db.Column(db.String(500), nullable=False, unique=True, index=True)
    hit_count = db.Column(db.Integer, default=0)
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    auto_blocked = db.Column(db.Boolean, default=False)
    reason = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'entity_type': self.entity_type,
            'entity_value': self.entity_value,
            'hit_count': self.hit_count,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'auto_blocked': self.auto_blocked,
            'reason': self.reason
        }


class Subscriber(db.Model):
    """Users subscribed to bulk alerts."""
    __tablename__ = 'subscribers'

    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    region = db.Column(db.String(50), nullable=True)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    alert_preferences = db.Column(db.Text, nullable=True)  # JSON object
    is_active = db.Column(db.Boolean, default=True, index=True)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'phone_number': self.phone_number,
            'region': self.region,
            'subscribed_at': self.subscribed_at.isoformat() if self.subscribed_at else None,
            'alert_preferences': json.loads(self.alert_preferences) if self.alert_preferences else {},
            'is_active': self.is_active
        }


class Campaign(db.Model):
    """Detected scam campaigns."""
    __tablename__ = 'campaigns'

    id = db.Column(db.Integer, primary_key=True)
    campaign_name = db.Column(db.String(200), nullable=False)
    pattern_description = db.Column(db.Text, nullable=True)
    affected_count = db.Column(db.Integer, default=0)
    first_detected = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_detected = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='active', index=True)  # 'active', 'resolved', 'archived'
    related_urls = db.Column(db.Text, nullable=True)  # JSON array
    related_phones = db.Column(db.Text, nullable=True)  # JSON array

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'campaign_name': self.campaign_name,
            'pattern_description': self.pattern_description,
            'affected_count': self.affected_count,
            'first_detected': self.first_detected.isoformat() if self.first_detected else None,
            'last_detected': self.last_detected.isoformat() if self.last_detected else None,
            'status': self.status,
            'related_urls': json.loads(self.related_urls) if self.related_urls else [],
            'related_phones': json.loads(self.related_phones) if self.related_phones else []
        }

