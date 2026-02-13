"""
Batch processor for campaign detection using Gemini.
"""
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from flask import current_app

from app.services.gemini.analyzer import GeminiAnalyzer
from app.services.gemini.prompt_templates import CAMPAIGN_DETECTION_PROMPT
from app.services.database.models import DatabaseService
from app.models import ScamLog

logger = logging.getLogger(__name__)


class CampaignDetector:
    """Service for detecting scam campaigns from batch analysis."""

    def __init__(self):
        """Initialize campaign detector."""
        self.analyzer = GeminiAnalyzer()
        self.threshold = current_app.config.get('CAMPAIGN_DETECTION_THRESHOLD', 5)

    def detect_campaigns(self, hours: int = 24) -> List[Dict]:
        """
        Detect campaigns from recent scam logs.

        Args:
            hours: Number of hours to look back

        Returns:
            List of detected campaigns
        """
        try:
            # Get recent scam logs
            recent_logs = DatabaseService.get_recent_scam_logs(hours=hours, limit=100)

            if len(recent_logs) < self.threshold:
                logger.info(f"Not enough reports ({len(recent_logs)}) for campaign detection")
                return []

            # Group logs by similarity (simple grouping by score and similar text)
            # For production, use more sophisticated clustering
            grouped_logs = self._group_similar_logs(recent_logs)

            # Analyze each group with Gemini
            detected_campaigns = []
            for group in grouped_logs:
                if len(group) >= self.threshold:
                    campaign = self._analyze_campaign_group(group)
                    if campaign:
                        detected_campaigns.append(campaign)

            logger.info(f"Detected {len(detected_campaigns)} campaigns")
            return detected_campaigns

        except Exception as e:
            logger.error(f"Error detecting campaigns: {e}")
            return []

    def _group_similar_logs(self, logs: List[ScamLog]) -> List[List[ScamLog]]:
        """
        Group similar scam logs together.

        Args:
            logs: List of ScamLog instances

        Returns:
            List of grouped logs
        """
        # Simple grouping: same score range and similar text length
        # In production, use semantic similarity or clustering
        groups = {}

        for log in logs:
            # Create a simple key for grouping
            score_range = (log.score // 2) * 2  # Group by score ranges
            text_length_range = (len(log.message_text) // 50) * 50  # Group by text length

            key = f"{score_range}_{text_length_range}"

            if key not in groups:
                groups[key] = []
            groups[key].append(log)

        # Return groups with at least threshold members
        return [group for group in groups.values() if len(group) >= self.threshold]

    def _analyze_campaign_group(self, logs: List[ScamLog]) -> Optional[Dict]:
        """
        Analyze a group of logs to detect a campaign.

        Args:
            logs: List of similar ScamLog instances

        Returns:
            Campaign dictionary or None
        """
        try:
            # Format messages for Gemini
            messages_text = []
            for i, log in enumerate(logs[:20], 1):  # Limit to 20 for context
                messages_text.append(
                    f"Message {i}:\n"
                    f"Text: {log.message_text[:200]}\n"
                    f"Sender: {log.original_sender}\n"
                    f"Score: {log.score}\n"
                )

            prompt = CAMPAIGN_DETECTION_PROMPT.format(
                count=len(logs),
                messages='\n\n'.join(messages_text)
            )

            # Use Vertex AI or Gemini API
            if self.analyzer.use_vertex_ai and hasattr(self.analyzer, 'model'):
                response = self.analyzer._analyze_with_vertex_ai(prompt)
            else:
                response = self.analyzer._analyze_with_gemini_api(prompt)

            # Parse response
            campaign_data = self._parse_campaign_response(response)

            if campaign_data and campaign_data.get('campaigns'):
                # Use first campaign detected
                campaign = campaign_data['campaigns'][0]

                # Extract URLs and phones from logs
                all_urls = set()
                all_phones = set()

                for log in logs:
                    if log.detected_urls:
                        try:
                            urls = json.loads(log.detected_urls)
                            all_urls.update(urls)
                        except:
                            pass
                    if log.original_sender:
                        all_phones.add(log.original_sender)

                campaign['urls'] = list(all_urls)
                campaign['phones'] = list(all_phones)
                campaign['affected_count'] = len(logs)

                return campaign

            return None

        except Exception as e:
            logger.error(f"Error analyzing campaign group: {e}")
            return None

    def _parse_campaign_response(self, response_text: str) -> Dict:
        """Parse campaign detection response."""
        try:
            text = response_text.strip()

            # Remove markdown code blocks if present
            if text.startswith('```'):
                lines = text.split('\n')
                text = '\n'.join(lines[1:-1]) if len(lines) > 2 else text

            # Find JSON object
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse campaign response: {e}")
            return {'campaigns': []}
