"""
Periodic campaign detection script.
Run this as a cron job or scheduled task.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from app.services.gemini.batch_processor import CampaignDetector
from app.services.database.models import DatabaseService
from app.services.notifications.alert_service import AlertService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

with app.app_context():
    try:
        # Initialize services
        detector = CampaignDetector()
        alert_service = AlertService()

        # Detect campaigns
        logger.info("Starting campaign detection...")
        campaigns = detector.detect_campaigns(hours=24)

        for campaign in campaigns:
            campaign_name = campaign.get('name', 'Unknown Campaign')
            affected_count = campaign.get('affected_count', 0)

            logger.info(f"Detected campaign: {campaign_name} ({affected_count} reports)")

            # Save campaign to database
            db_campaign = DatabaseService.create_campaign(
                campaign_name=campaign_name,
                pattern_description=campaign.get('pattern', ''),
                related_urls=campaign.get('urls', []),
                related_phones=campaign.get('phones', [])
            )

            # Send bulk alert
            if app.config.get('ENABLE_BULK_ALERTS', True):
                result = alert_service.send_campaign_alert(
                    campaign_name=campaign_name,
                    affected_count=affected_count
                )
                logger.info(f"Alert sent: {result}")

        logger.info(f"Campaign detection complete. Found {len(campaigns)} campaigns.")

    except Exception as e:
        logger.error(f"Error in campaign detection: {e}", exc_info=True)
        sys.exit(1)

