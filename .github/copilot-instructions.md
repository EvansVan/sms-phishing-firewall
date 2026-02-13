# Copilot Instructions: SMS Phishing Firewall

## Project Overview

A Flask application that detects SMS phishing/scams by integrating Africa's Talking (SMS/USSD provider) with Google's Gemini/Vertex AI for real-time threat analysis. The app maintains a community blacklist, detects campaigns from multiple reports, and sends bulk alerts to subscribers.

**Data flow:** Africa's Talking webhook → Flask route → Gemini analyzer → Database → Blacklist/Alerts

## Architecture Patterns

### 1. Service Layer Organization

The codebase uses a strict service-oriented architecture to separate concerns:

```
app/
├── routes/              # HTTP endpoints (webhooks only)
├── services/            # Business logic (DO NOT import into models.py)
│   ├── database/        # DatabaseService (models.py & blacklist.py)
│   ├── gemini/          # GeminiAnalyzer (Vertex AI or API SDK)
│   ├── africas_talking/ # SMS/USSD provider integration
│   └── notifications/   # AlertService, SocialMediaService
├── models.py            # SQLAlchemy ORM classes (no business logic)
└── config.py            # Config with os.getenv() defaults
```

**Key rule:** Routes call services; services call database; database calls ORM models. Never reverse this dependency.

### 2. AI Provider Abstraction (Gemini vs. Vertex AI)

[app/services/gemini/analyzer.py](app/services/gemini/analyzer.py) supports two backends via `USE_VERTEX_AI` config flag:
- **Vertex AI (GCP):** Production-grade, requires `GCP_PROJECT_ID` and gcloud auth
- **Gemini API SDK:** Development/testing, only requires `GEMINI_API_KEY`

**Pattern:** Try Vertex AI imports first, fall back to Gemini API. Check `current_app.config.get('USE_VERTEX_AI')` at runtime. Both use the same `analyze_message()` method signature.

### 3. Environment Variable Loading

**Critical:** `.env` must be loaded early. Both [run.py](run.py) and [scripts/init_db.py](scripts/init_db.py) call `load_dotenv()` at the top. Add this to any new entry point (CLI scripts, async workers) before importing `app`.

Config defaults in [app/config.py](app/config.py) use `os.getenv()` with fallbacks (e.g., `AT_USERNAME='sandbox'` for testing). Database URL defaults to `sqlite:///` in the repo root if `DATABASE_URL` not set.

### 4. Webhook Security & Validation

[app/routes/sms_webhook.py](app/routes/sms_webhook.py) implements:
- Signature verification (`verify_webhook_signature_from_request`)
- IP whitelist (`AT_WEBHOOK_IP_WHITELIST` list of strings)
- Replay attack prevention (nonce deduplication)
- Request data validation via `@validate_request_data` decorator

**Pattern:** Always run security checks before service initialization. If any check fails, return early with a specific HTTP error code (401 for signature, 403 for IP, 409 for replay).

### 5. Service Initialization Pattern

Services are lazily initialized in routes via module-level globals and an `init_services()` helper (see [sms_webhook.py lines 33–51](app/routes/sms_webhook.py#L33-L51)). This ensures they are created within the Flask app context (required for `current_app.config`).

**Pattern:** Replicate this for any new route blueprint or async worker to avoid app context errors.

## Database & ORM

### Model Definition vs. Service Logic

- **[app/models.py](app/models.py):** SQLAlchemy model classes (`ScamLog`, `Blacklist`, `Subscriber`, `Campaign`). Contains only schema and `to_dict()` serialization methods. Zero business logic.
- **[app/services/database/models.py](app/services/database/models.py):** `DatabaseService` class with static methods for CRUD (`save_scam_log`, `add_to_blacklist`, `is_blacklisted`, `get_subscribers`, `create_campaign`). Handles transactions, logging, and error rollback.

**Naming confusion note:** Consider renaming `app/services/database/models.py` to `database_service.py` in future refactoring. All imports currently target `DatabaseService` by class name, so a rename is low-risk.

### Blacklist Logic

[app/services/database/blacklist.py](app/services/database/blacklist.py) wraps blacklist operations in `BlacklistService`:
- `check_and_add_to_blacklist(score, phone, url)` — auto-adds entries if danger score exceeds thresholds
- `is_entity_blacklisted(phone, url)` — checks both tables

Thresholds are configurable: `BLACKLIST_SCORE_THRESHOLD` (default 8) for phones, `URL_BLACKLIST_SCORE_THRESHOLD` (default 9) for URLs.

## Common Workflows

### Adding a New Webhook Endpoint

1. Create a route in [app/routes/ussd_webhook.py](app/routes/ussd_webhook.py) or [app/routes/sms_webhook.py](app/routes/sms_webhook.py)
2. Add security checks (signature, IP whitelist, replay prevention)
3. Initialize services via `init_services()` helper
4. Extract and validate input using [app/utils/validators.py](app/utils/validators.py) functions
5. Call appropriate service methods (Gemini analyzer, DatabaseService, AlertService)
6. Return JSON response with status and relevant data

Example: `sms_webhook.py` flow at [lines 55–202](app/routes/sms_webhook.py#L55-L202).

### Running Database Initialization

```bash
# Ensure .env is in repo root with AT_USERNAME and AT_API_KEY set
python scripts/init_db.py
# Creates tables: scam_logs, blacklist, subscribers, campaigns
```

The script imports `create_app` and calls `db.create_all()` within app context. Do not modify without ensuring `load_dotenv()` runs first.

### Testing Against Africa's Talking Sandbox

[test_at_api.py](test_at_api.py) demonstrates the expected workflow:
```python
from dotenv import load_dotenv
load_dotenv()
username = os.getenv('AT_USERNAME')  # 'sandbox' for dev
api_key = os.getenv('AT_API_KEY')
africastalking.initialize(username, api_key)
sms = africastalking.SMS
sms.send("message", ["+254712345678"])
```

For development, use `AT_USERNAME='sandbox'` and a sandbox API key from Africa's Talking dashboard.

## Key Files & Their Roles

| File | Purpose |
|------|---------|
| [app/__init__.py](app/__init__.py) | App factory, blueprint registration, db initialization |
| [app/config.py](app/config.py) | Config classes (Development, Production, Testing); env var defaults |
| [app/models.py](app/models.py) | ORM model classes for all tables |
| [run.py](run.py) | Entry point; loads .env and creates app |
| [scripts/init_db.py](scripts/init_db.py) | Database initialization; loads .env before importing app |
| [app/routes/sms_webhook.py](app/routes/sms_webhook.py) | Main SMS webhook handler; full example of security + service flow |
| [app/services/database/models.py](app/services/database/models.py) | DatabaseService with all CRUD methods |
| [app/services/gemini/analyzer.py](app/services/gemini/analyzer.py) | GeminiAnalyzer; abstracts Vertex AI vs. Gemini API |
| [app/utils/validators.py](app/utils/validators.py) | Input validation, URL/phone extraction, sanitization |
| [app/utils/security.py](app/utils/security.py) | Webhook signature, IP whitelist, replay prevention |

## Conventions & Gotchas

- **Lazy service initialization:** Services are global singletons initialized on first route call. Avoid importing services at module level in routes.
- **Database context:** Always ensure code runs within `app.app_context()` if using `db.session` or `current_app.config`. Routes do this automatically; scripts must wrap logic.
- **`current_app` import:** Always import from `flask`, not from `app`. [app/services/database/blacklist.py](app/services/database/blacklist.py) had this bug initially (fixed).
- **Config defaults:** [app/config.py](app/config.py) provides sensible defaults (e.g., `AT_USERNAME='sandbox'`, SQLite DB at repo root). Override via `.env` or environment variables.
- **JSON fields in DB:** `analysis_json`, `detected_urls`, `related_urls`, `related_phones` are stored as JSON text; use `json.dumps()` on write, `json.loads()` on read (see [DatabaseService.save_scam_log](app/services/database/models.py#L18-L60)).
- **Error handling:** Services catch exceptions, rollback transactions, and log before re-raising. Routes catch and return 500 with logged traceback.

## Testing & Debugging

- **Check .env loaded:** `python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('AT_USERNAME'))"`
- **DNS issues (NameResolutionError for Africa's Talking API):** Run `host api.sandbox.africastalking.com` or `curl -v https://api.sandbox.africastalking.com/version1/messaging`
- **Test database operations:** Run [test_database.py](test_database.py) to create sample ScamLog and Blacklist entries
- **Test Gemini analyzer:** Run [test_gemini_analyzer.py](test_gemini_analyzer.py) (ensure `GEMINI_API_KEY` set)

## Quick Start (Dev)

```bash
source ATXGCP/bin/activate  # or: python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Create .env with AT_USERNAME, AT_API_KEY, GEMINI_API_KEY
python scripts/init_db.py
python run.py  # Starts Flask at http://localhost:5000
```
