# SMS Phishing Firewall: Community Immune System

A production-ready Flask application that integrates Africa's Talking (SMS/USSD) with Google Cloud AI (Gemini/Vertex AI) to create a community-driven phishing detection and education platform.

## Features

- **Real-time Threat Analysis**: Uses Gemini AI to analyze forwarded SMS messages for phishing/scam indicators
- **Community Blacklist**: Automatically blacklists high-risk phone numbers and URLs
- **Campaign Detection**: Identifies scam campaigns from multiple reports using batch analysis
- **Bulk Alerts**: Sends SMS alerts to subscribers when campaigns are detected
- **Multi-channel Support**: SMS forwarding and USSD reporting
- **Educational Responses**: Provides users with educational tips about detected scams

## Architecture

```
User forwards SMS → Africa's Talking → Flask Webhook → Gemini AI Analysis
                                                      ↓
                                    Database ← Blacklist System
                                                      ↓
                                    Bulk Alerts → Subscribers
```

## Prerequisites

- Python 3.11+
- Africa's Talking account and API credentials
- Google Cloud AI API key (Gemini) or GCP project with Vertex AI enabled
- PostgreSQL (for production) or SQLite (for development)

## Installation

1. **Clone the repository**
   ```bash
   cd sms-phishing-firewall
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Initialize database**
   ```bash
   python scripts/init_db.py
   ```

## Configuration

### Environment Variables

Key configuration variables (see `.env.example` for full list):

- `AT_USERNAME`: Africa's Talking username (use 'sandbox' for testing)
- `AT_API_KEY`: Africa's Talking API key
- `AT_SHORTCODE`: Your shortcode for receiving forwarded messages
- `GEMINI_API_KEY`: Google Gemini API key (if using Gemini API SDK)
- `USE_VERTEX_AI`: Set to 'true' to use Vertex AI instead of Gemini API
- `GCP_PROJECT_ID`: GCP project ID (required for Vertex AI)
- `DATABASE_URL`: Database connection string

### Africa's Talking Setup

1. Create an account at [Africa's Talking](https://africastalking.com)
2. Create an application and get your API key
3. Configure webhook URLs in your dashboard:
   - SMS: `https://your-domain.com/webhook/sms`
   - USSD: `https://your-domain.com/webhook/ussd`

### Google Cloud AI Setup

**Option 1: Gemini API SDK (Recommended for development)**
1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set `GEMINI_API_KEY` in `.env`

**Option 2: Vertex AI (Recommended for production)**
1. Enable Vertex AI API in your GCP project
2. Set up authentication (service account or gcloud)
3. Set `USE_VERTEX_AI=true` and `GCP_PROJECT_ID` in `.env`

## Running the Application

### Development

```bash
python run.py
```

The application will run on `http://localhost:5000`

### Production with Docker

```bash
docker-compose up -d
```

### Production on GCP Cloud Run

1. Build and push Docker image:
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```

2. Or deploy manually:
   ```bash
   gcloud run deploy sms-phishing-firewall \
     --source . \
     --region us-central1 \
     --allow-unauthenticated
   ```

## API Endpoints

### Webhooks (called by Africa's Talking)

- `POST /webhook/sms` - Receive forwarded SMS messages
- `POST /webhook/ussd` - Handle USSD session requests

### Health Check

- `GET /health` - Application health status

## Usage Flow

1. **User forwards suspicious SMS** to your shortcode (e.g., 22334)
2. **Africa's Talking** sends webhook to `/webhook/sms`
3. **Gemini AI** analyzes the message for phishing indicators
4. **System** stores analysis in database
5. **Blacklist** is updated if score exceeds threshold
6. **User receives** educational response via SMS
7. **Campaign detection** runs periodically to identify mass scams
8. **Bulk alerts** are sent to subscribers when campaigns are detected

## Database Schema

- **ScamLog**: Stores all reported messages and analysis results
- **Blacklist**: Community blacklist of phone numbers and URLs
- **Subscriber**: Users subscribed to bulk alerts
- **Campaign**: Detected scam campaigns

## Security Features

- Input validation and sanitization
- Rate limiting on webhook endpoints
- SQL injection prevention (parameterized queries)
- Secure API key management via environment variables
- Request validation

## Development

### Running Tests

```bash
pytest app/tests/
```

### Database Migrations

```bash
flask db init
flask db migrate -m "Description"
flask db upgrade
```

## Deployment

### GCP Cloud Run

1. Ensure `cloudbuild.yaml` is configured
2. Connect your repository to Cloud Build
3. Push to trigger automatic deployment

### Manual Deployment

1. Build Docker image:
   ```bash
   docker build -t sms-phishing-firewall .
   ```

2. Run container:
   ```bash
   docker run -p 5000:5000 --env-file .env sms-phishing-firewall
   ```

## Monitoring

- Application logs are output to stdout/stderr
- In GCP, logs are automatically collected in Cloud Logging
- Set up Cloud Monitoring alerts for error rates and latency

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License

## Support

For issues and questions:
- Check the [documentation](docs/)
- Open an issue on GitHub
- Contact the development team

## Acknowledgments

- Africa's Talking for SMS/USSD APIs
- Google Cloud AI for Gemini/Vertex AI capabilities
- The Kenyan cybersecurity community for inspiration

