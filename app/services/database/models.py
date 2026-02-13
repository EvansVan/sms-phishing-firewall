"""
Database operations for SMS Phishing Firewall.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from app import db
from app.models import ScamLog, Blacklist, Subscriber, Campaign
import json
import logging

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for database operations."""

    @staticmethod
    def save_scam_log(
        reporter_phone: str,
        message_text: str,
        score: int,
        original_sender: Optional[str] = None,
        analysis_json: Optional[Dict] = None,
        detected_urls: Optional[List[str]] = None,
        is_campaign: bool = False
    ) -> ScamLog:
        """
        Save a scam log entry.

        Args:
            reporter_phone: Phone number of the reporter
            message_text: The scam message text
            score: Danger score from Gemini
            original_sender: Original sender phone number
            analysis_json: Full analysis from Gemini
            detected_urls: List of detected URLs
            is_campaign: Whether this is part of a campaign

        Returns:
            Created ScamLog instance
        """
        try:
            scam_log = ScamLog(
                reporter_phone=reporter_phone,
                original_sender=original_sender,
                message_text=message_text,
                score=score,
                analysis_json=json.dumps(analysis_json) if analysis_json else None,
                detected_urls=json.dumps(detected_urls) if detected_urls else None,
                is_campaign=is_campaign
            )
            db.session.add(scam_log)
            db.session.commit()
            logger.info(f"Saved scam log: ID={scam_log.id}, Score={score}")
            return scam_log
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving scam log: {e}")
            raise

    @staticmethod
    def get_recent_scam_logs(hours: int = 24, limit: int = 100) -> List[ScamLog]:
        """
        Get recent scam logs.

        Args:
            hours: Number of hours to look back
            limit: Maximum number of logs to return

        Returns:
            List of ScamLog instances
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return ScamLog.query.filter(
            ScamLog.timestamp >= cutoff_time
        ).order_by(
            ScamLog.timestamp.desc()
        ).limit(limit).all()

    @staticmethod
    def add_to_blacklist(
        entity_type: str,
        entity_value: str,
        auto_blocked: bool = False,
        reason: Optional[str] = None
    ) -> Blacklist:
        """
        Add entity to blacklist or update existing entry.

        Args:
            entity_type: 'phone' or 'url'
            entity_value: The entity to blacklist
            auto_blocked: Whether automatically blocked
            reason: Reason for blacklisting

        Returns:
            Blacklist instance
        """
        try:
            # Check if already exists
            existing = Blacklist.query.filter_by(
                entity_type=entity_type,
                entity_value=entity_value
            ).first()

            if existing:
                existing.hit_count += 1
                existing.last_seen = datetime.utcnow()
                if auto_blocked:
                    existing.auto_blocked = True
                if reason:
                    existing.reason = reason
                db.session.commit()
                logger.info(f"Updated blacklist entry: {entity_type}={entity_value}")
                return existing
            else:
                blacklist_entry = Blacklist(
                    entity_type=entity_type,
                    entity_value=entity_value,
                    hit_count=1,
                    auto_blocked=auto_blocked,
                    reason=reason
                )
                db.session.add(blacklist_entry)
                db.session.commit()
                logger.info(f"Added to blacklist: {entity_type}={entity_value}")
                return blacklist_entry
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding to blacklist: {e}")
            raise

    @staticmethod
    def is_blacklisted(entity_type: str, entity_value: str) -> bool:
        """
        Check if entity is blacklisted.

        Args:
            entity_type: 'phone' or 'url'
            entity_value: The entity to check

        Returns:
            True if blacklisted
        """
        return Blacklist.query.filter_by(
            entity_type=entity_type,
            entity_value=entity_value
        ).first() is not None

    @staticmethod
    def get_subscribers(region: Optional[str] = None, active_only: bool = True) -> List[Subscriber]:
        """
        Get subscribers for bulk alerts.

        Args:
            region: Filter by region (optional)
            active_only: Only return active subscribers

        Returns:
            List of Subscriber instances
        """
        query = Subscriber.query
        if active_only:
            query = query.filter_by(is_active=True)
        if region:
            query = query.filter_by(region=region)
        return query.all()

    @staticmethod
    def create_or_update_subscriber(
        phone_number: str,
        region: Optional[str] = None,
        alert_preferences: Optional[Dict] = None
    ) -> Subscriber:
        """
        Create or update a subscriber.

        Args:
            phone_number: Subscriber phone number
            region: Subscriber region
            alert_preferences: Alert preferences as dict

        Returns:
            Subscriber instance
        """
        try:
            subscriber = Subscriber.query.filter_by(phone_number=phone_number).first()

            if subscriber:
                if region:
                    subscriber.region = region
                if alert_preferences:
                    subscriber.alert_preferences = json.dumps(alert_preferences)
                subscriber.is_active = True
                db.session.commit()
                return subscriber
            else:
                subscriber = Subscriber(
                    phone_number=phone_number,
                    region=region,
                    alert_preferences=json.dumps(alert_preferences) if alert_preferences else None
                )
                db.session.add(subscriber)
                db.session.commit()
                return subscriber
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating/updating subscriber: {e}")
            raise

    @staticmethod
    def create_campaign(
        campaign_name: str,
        pattern_description: Optional[str] = None,
        related_urls: Optional[List[str]] = None,
        related_phones: Optional[List[str]] = None
    ) -> Campaign:
        """
        Create a new campaign record.

        Args:
            campaign_name: Name of the campaign
            pattern_description: Description of the pattern
            related_urls: List of related URLs
            related_phones: List of related phone numbers

        Returns:
            Campaign instance
        """
        try:
            campaign = Campaign(
                campaign_name=campaign_name,
                pattern_description=pattern_description,
                related_urls=json.dumps(related_urls) if related_urls else None,
                related_phones=json.dumps(related_phones) if related_phones else None,
                affected_count=1
            )
            db.session.add(campaign)
            db.session.commit()
            logger.info(f"Created campaign: {campaign_name}")
            return campaign
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating campaign: {e}")
            raise

    @staticmethod
    def update_campaign(campaign_id: int, affected_count: Optional[int] = None) -> Campaign:
        """
        Update campaign statistics.

        Args:
            campaign_id: Campaign ID
            affected_count: New affected count (optional)

        Returns:
            Updated Campaign instance
        """
        try:
            campaign = Campaign.query.get(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")

            if affected_count is not None:
                campaign.affected_count = affected_count
            campaign.last_detected = datetime.utcnow()
            db.session.commit()
            return campaign
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating campaign: {e}")
            raise

