"""
Gemini AI Analyzer for threat detection.
"""
import importlib
import json
import logging
from typing import Dict, Optional, List
from flask import current_app

logger = logging.getLogger(__name__)

try:
    # Try Vertex AI first (for GCP)
    from google.cloud import aiplatform
    VERTEX_AI_AVAILABLE = True
except ImportError:
    aiplatform = None
    VERTEX_AI_AVAILABLE = False

try:
    # Fallback to Gemini API SDK
    from google import genai
    GEMINI_API_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_API_AVAILABLE = False

from app.services.gemini.prompt_templates import SYSTEM_INSTRUCTION, ANALYSIS_PROMPT_TEMPLATE


class GeminiAnalyzer:
    """Service for analyzing SMS messages with Gemini AI."""

    def __init__(self):
        """Initialize Gemini client."""
        self.use_vertex_ai = current_app.config.get('USE_VERTEX_AI', False)
        self.model_name = current_app.config.get('GEMINI_MODEL', 'gemini-2.0-flash')
        self.model_candidates = self._build_model_candidates()

        if self.use_vertex_ai and VERTEX_AI_AVAILABLE:
            self._init_vertex_ai()
        elif GEMINI_API_AVAILABLE:
            self._init_gemini_api()
        else:
            logger.error("Neither Vertex AI nor Gemini API SDK available")
            raise ImportError("Please install google-cloud-aiplatform or google-genai")

    def _build_model_candidates(self) -> List[str]:
        """Build ordered list of model candidates for Gemini API fallback."""
        configured_candidates = current_app.config.get('GEMINI_MODEL_CANDIDATES', '')
        fallback_models = [
            'gemini-2.0-flash',
            'gemini-2.0-flash-lite',
            'gemini-1.5-flash',
            'gemini-1.5-flash-latest',
            'gemini-1.5-pro'
        ]

        candidates = []
        if self.model_name:
            candidates.append(self.model_name)

        if configured_candidates:
            for model in configured_candidates.split(','):
                model = model.strip()
                if model and model not in candidates:
                    candidates.append(model)

        for model in fallback_models:
            if model not in candidates:
                candidates.append(model)

        return candidates

    def _init_vertex_ai(self):
        """Initialize Vertex AI client."""
        if aiplatform is None:
            raise ImportError("google-cloud-aiplatform is not available")

        project_id = current_app.config.get('GCP_PROJECT_ID')
        location = current_app.config.get('GCP_LOCATION', 'us-central1')

        if not project_id:
            raise ValueError("GCP_PROJECT_ID required for Vertex AI")

        aiplatform.init(project=project_id, location=location)
        generative_models = importlib.import_module('vertexai.generative_models')
        model_class = getattr(generative_models, 'GenerativeModel')
        self.model = model_class(self.model_name)
        logger.info(f"Initialized Vertex AI with model: {self.model_name}")

    def _init_gemini_api(self):
        """Initialize Gemini API SDK client."""
        if genai is None:
            raise ImportError("google-genai SDK is not available")

        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY required")

        self.client = genai.Client(api_key=api_key)
        logger.info(f"Initialized Gemini API SDK with preferred model: {self.model_name}")

    def analyze_message(
        self,
        message_text: str,
        sender: Optional[str] = None,
        urls: Optional[List[str]] = None,
        phones: Optional[List[str]] = None
    ) -> Dict:
        """
        Analyze SMS message for phishing/scam indicators.

        Args:
            message_text: The SMS message text
            sender: Sender phone number (optional)
            urls: Detected URLs in message (optional)
            phones: Detected phone numbers in message (optional)

        Returns:
            Analysis dictionary with score, summary, lesson, etc.
        """
        try:
            # Format URLs and phones for prompt
            urls_str = ', '.join(urls) if urls else 'None'
            phones_str = ', '.join(phones) if phones else 'None'
            sender_str = sender or 'Unknown'

            # Build prompt
            prompt = ANALYSIS_PROMPT_TEMPLATE.format(
                message_text=message_text,
                sender=sender_str,
                urls=urls_str,
                phones=phones_str
            )

            # Get response from Gemini
            if self.use_vertex_ai and hasattr(self, 'model'):
                response = self._analyze_with_vertex_ai(prompt)
            else:
                response = self._analyze_with_gemini_api(prompt)

            # Parse JSON response
            analysis = self._parse_response(response)

            # Validate and set defaults
            analysis.setdefault('score', 5)
            analysis.setdefault('summary', 'Message analyzed')
            analysis.setdefault('lesson', 'Be cautious with suspicious messages')
            analysis.setdefault('is_campaign', False)
            analysis.setdefault('techniques', [])
            analysis.setdefault('confidence', 0.8)

            # Ensure score is in valid range
            analysis['score'] = max(1, min(10, int(analysis['score'])))

            logger.info(f"Analysis complete: Score={analysis['score']}, Campaign={analysis['is_campaign']}")
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing message: {e}")
            # Return safe default
            return {
                'score': 5,
                'summary': 'Analysis error occurred',
                'lesson': 'Please forward suspicious messages to our shortcode',
                'is_campaign': False,
                'techniques': [],
                'confidence': 0.0,
                'error': str(e)
            }

    def _analyze_with_vertex_ai(self, prompt: str) -> str:
        """Analyze using Vertex AI."""
        generation_config = {
            "temperature": 0.3,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1024,
        }

        response = self.model.generate_content(
            contents=[SYSTEM_INSTRUCTION, prompt],
            generation_config=generation_config
        )

        return response.text or ''

    def _analyze_with_gemini_api(self, prompt: str) -> str:
        """Analyze using Gemini API SDK."""
        # Combine system instruction with prompt for Gemini API
        # (Gemini API only accepts "user" and "model" roles, not "system")
        combined_prompt = f"{SYSTEM_INSTRUCTION}\n\n{prompt}"
        last_error = None

        for model in self.model_candidates:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=[
                        {"role": "user", "parts": [{"text": combined_prompt}]}
                    ]
                )

                if model != self.model_name:
                    logger.warning(
                        f"Model '{self.model_name}' unavailable, switched to '{model}'"
                    )
                    self.model_name = model

                return response.text or ''
            except Exception as e:
                error_text = str(e)
                last_error = e
                model_not_found = '404' in error_text or 'NOT_FOUND' in error_text

                if model_not_found:
                    logger.warning(f"Gemini model unavailable: {model}, trying fallback")
                    continue

                raise

        raise RuntimeError(
            f"No compatible Gemini model found. Tried: {', '.join(self.model_candidates)}"
        ) from last_error

    def _parse_response(self, response_text: str) -> Dict:
        """
        Parse JSON response from Gemini.

        Args:
            response_text: Raw response text

        Returns:
            Parsed dictionary
        """
        # Try to extract JSON from response
        # Sometimes Gemini wraps JSON in markdown code blocks
        text = response_text.strip()

        # Remove markdown code blocks if present
        if text.startswith('```'):
            lines = text.split('\n')
            text = '\n'.join(lines[1:-1]) if len(lines) > 2 else text

        # Try to find JSON object
        try:
            # Look for JSON object
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Try parsing entire text
                return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            logger.warning(f"Response text: {response_text[:200]}")
            # Try to extract score from text as fallback
            import re
            score_match = re.search(r'score["\']?\s*[:=]\s*(\d+)', text, re.IGNORECASE)
            score = int(score_match.group(1)) if score_match else 5

            return {
                'score': score,
                'summary': 'Could not parse full analysis',
                'lesson': 'Be cautious with suspicious messages',
                'is_campaign': False,
                'techniques': [],
                'confidence': 0.5
            }

