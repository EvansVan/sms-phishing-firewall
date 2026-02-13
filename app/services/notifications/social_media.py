"""
Social media posting service.
"""
import logging
from typing import Optional
from flask import current_app

logger = logging.getLogger(__name__)

# Try to import tweepy (optional dependency)
try:
    import tweepy
    TWITTER_AVAILABLE = True
except ImportError:
    TWITTER_AVAILABLE = False
    logger.warning("tweepy not installed, Twitter posting disabled")


class SocialMediaService:
    """Service for posting to social media."""

    def __init__(self):
        """Initialize social media service."""
        self.enabled = current_app.config.get('ENABLE_SOCIAL_MEDIA', False)
        self.twitter_client = None

        if self.enabled and TWITTER_AVAILABLE:
            self._init_twitter()

    def _init_twitter(self):
        """Initialize Twitter client."""
        try:
            api_key = current_app.config.get('TWITTER_API_KEY')
            api_secret = current_app.config.get('TWITTER_API_SECRET')
            access_token = current_app.config.get('TWITTER_ACCESS_TOKEN')
            access_token_secret = current_app.config.get('TWITTER_ACCESS_TOKEN_SECRET')

            if all([api_key, api_secret, access_token, access_token_secret]):
                auth = tweepy.OAuthHandler(api_key, api_secret)
                auth.set_access_token(access_token, access_token_secret)
                self.twitter_client = tweepy.API(auth)
                logger.info("Twitter client initialized")
            else:
                logger.warning("Twitter credentials incomplete")
        except Exception as e:
            logger.error(f"Error initializing Twitter client: {e}")

    def post_campaign_alert(
        self,
        scam_text: str,
        lesson: str,
        score: int
    ) -> dict:
        """
        Post campaign alert to social media.

        Args:
            scam_text: The scam message text
            lesson: Educational lesson
            score: Danger score

        Returns:
            Result dictionary
        """
        if not self.enabled:
            return {'success': False, 'reason': 'disabled'}

        try:
            # Format tweet
            scam_preview = scam_text[:50] + "..." if len(scam_text) > 50 else scam_text
            tweet = (
                f"🚨 SCAM ALERT: '{scam_preview}'\n\n"
                f"💡 Tip: {lesson}\n"
                f"Score: {score}/10 #CyberSecurityKenya #StaySafe"
            )

            # Post to Twitter if available
            if self.twitter_client:
                response = self.twitter_client.update_status(tweet)
                logger.info(f"Posted to Twitter: {response.id}")
                return {
                    'success': True,
                    'platform': 'twitter',
                    'tweet_id': response.id
                }
            else:
                logger.warning("Twitter client not available")
                return {'success': False, 'reason': 'twitter_not_configured'}

        except Exception as e:
            logger.error(f"Error posting to social media: {e}")
            return {'success': False, 'error': str(e)}

