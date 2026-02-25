# Complete Deployment Guide
**Estimated Time:** 3-4 hours (1-2 hours if you've done GCP before)

---

## Table of Contents
1. [Quick Checklist](#quick-checklist) — Just the commands to run
2. [Phase 1: Repository Setup](#phase-1-repository-setup) — Git branches & cleanup
3. [Phase 2: Google Colab Demo](#phase-2-google-colab-demo) — Shareable notebook
4. [Phase 3: Cloud Run Production](#phase-3-cloud-run-production) — Live endpoint
5. [Verification & Testing](#verification--testing) — Make sure everything works
6. [Troubleshooting](#troubleshooting) — Common issues and fixes
7. [File Reference](#file-reference) — What goes where

---

## Quick Checklist

Run these commands in order:

```bash
cd ~/Desktop/AT\ \&\ Gemini/sms-phishing-firewall

# PHASE 1: Setup branches (production branch for deployment)
git checkout main                          # Start on main
git branch production                      # Create production branch
git checkout production                    # Switch to production
rm -f test_*.py test_*.md GETTING_STARTED.md QUICK_START.md WEBHOOK_SECURITY.md
rm -f scripts/demo_evaluation.py scripts/seed_data.py create_test_campaign.py
rm -rf instance/
git add -A
git commit -m "Deployment: Clean version for Cloud Run (production branch)"
git checkout main                          # Back to main

# PHASE 1B: Push main to Github (your primary repo)
git push origin main

# PHASE 2: Colab (manual steps at Step 2.1 below)

# PHASE 3: Cloud Run (deploy from production branch)
gcloud auth login
gcloud projects create sms-phishing-firewall
gcloud config set project sms-phishing-firewall
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com

echo -n "your-gemini-key" | gcloud secrets create GEMINI_API_KEY --data-file=-
echo -n "your-at-key" | gcloud secrets create AT_API_KEY --data-file=-
echo -n "sandbox" | gcloud secrets create AT_USERNAME --data-file=-

git checkout production                    # Switch to production branch
chmod +x scripts/deploy_cloud_run.sh
./scripts/deploy_cloud_run.sh sms-phishing-firewall sms-firewall us-central1

# Get URL and configure Africa's Talking webhook
gcloud run services describe sms-firewall --region us-central1 --format='value(status.url)'
```

---

## Phase 1: Repository Setup

### Step 1.1: Understand the Strategy

**Git Branch Strategy:**
- `main` branch = Your full repository (all code, tests gitignored)
  - Push to Github
  - Judges see this when they clone
  - Contains all production code
- `production` branch = Clean deployment version (for Cloud Run only)
  - Used only for GCP/Cloud Run deployment
  - Removes test files from git tracking
  - Never push to Github
  
**Why this works:**
- Main stays intact for Github (no weird deletions)
- Production is a clean deployment branch
- Test files are gitignored on main anyway

### Step 1.2: Create Production Branch for Deployment

```bash
cd ~/Desktop/AT\ \&\ Gemini/sms-phishing-firewall

# Make sure you're on main (your full code)
git checkout main

# Create production branch from main (for deployment only)
git branch production

# Switch to production
git checkout production

# Verify you're on production
git branch --show-current
# Should output: production
```

### Step 1.3: Clean Files on Production Branch

```bash
# Only delete files from the production branch (not main)
# These deletions stay on production, main is untouched

# Remove test files
rm -f test_*.py test_*.md *_test.py

# Remove dev documentation
rm -f GETTING_STARTED.md QUICK_START.md WEBHOOK_SECURITY.md

# Remove dev-only scripts
rm -f scripts/demo_evaluation.py scripts/seed_data.py create_test_campaign.py

# Remove database artifacts (will regenerate on Cloud Run)
rm -rf instance/

# Verify what will be deleted
git status
# Should show files under "Changes not staged for commit"
```

### Step 1.4: Commit Cleanup on Production Branch

```bash
# Stage all deletions (only on production branch)
git add -A

# Commit with clear message
git commit -m "Deployment: Clean version for Cloud Run

- Remove test_*.py, test_*.md (all test files)
- Remove GETTING_STARTED.md, QUICK_START.md, WEBHOOK_SECURITY.md
- Remove dev-only scripts (demo_evaluation.py, seed_data.py, create_test_campaign.py)
- Clean up database artifacts (instance/ directory)

This is the production branch for Cloud Run deployment.
Main branch remains unchanged with all files."
```

### Step 1.5: Return to Main Branch

```bash
# Switch back to main (stays untouched)
git checkout main

# Verify main still has everything
git ls-files | grep -i "GETTING_STARTED\|test_at"
# Should show files (they're here, just gitignored)

# See your branches
git branch -a
# Should show:
#   main
# * production
```

### Step 1.6: Push Main to Github

```bash
# Push only main to Github (your public repository)
git push origin main

# Do NOT push production to Github (it's local only for deployment)

# Verify
git branch -r
# Should show:
#   origin/main (your repo)
# (no production there)

### Step 1.5: Verify Environment Files

```bash
# Ensure .env.example exists and has required variables
cat .env.example

# Should include:
# AT_USERNAME, AT_API_KEY
# GEMINI_API_KEY or USE_VERTEX_AI + GCP_PROJECT_ID
# DATABASE_URL, FLASK_ENV, SECRET_KEY
# LOG_LEVEL
```

**If missing, create:**

```bash
cat > .env.example << 'EOF'
# Africa's Talking Configuration
AT_USERNAME=sandbox
AT_API_KEY=your_api_key_here
AT_SHORTCODE=22334
AT_WEBHOOK_IP_WHITELIST=5.153.127.0/24,196.216.217.0/24

# Google Cloud Configuration
USE_VERTEX_AI=true
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1

# Gemini Configuration (if not using Vertex AI)
GEMINI_API_KEY=your_gemini_key

# Database Configuration
DATABASE_URL=sqlite:///firewall.db

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-change-in-production

# Optional
LOG_LEVEL=INFO
EOF

git add .env.example
git commit -m "Add .env.example template"
git push origin main
```

### Step 1.7: (Optional) Set Default Branch on Github

1. Go to: https://github.com/your-username/sms-phishing-firewall
2. Click: **Settings → Branches**
3. Under "Default branch": select **main**
4. Click: **Update**

This ensures judges clone the full main branch by default.

**✅ Phase 1 Complete:** 
- `main` branch pushed to Github (complete code, tests gitignored)
- `production` branch ready locally for Cloud Run deployment

---

## Phase 2: Google Colab Demo

### Step 2.1: Create Colab Notebook

This gives judges a shareable, no-setup demo they can run in seconds.

**Option A: Create Manually in Colab (Recommended)**

1. Go to: https://colab.research.google.com
2. Click: **"+ New notebook"**
3. Name it: `"SMS Phishing Firewall Demo"`
4. Add cells below (copy-paste each cell)

**Option B: Upload Existing Notebook**

Use [COLAB_DEPLOYMENT.md](COLAB_DEPLOYMENT.md) if you have a pre-built notebook.

### Step 2.2: Add Colab Cells

#### Cell 1: Clone & Setup
```python
# Clone repository and install dependencies
!git clone https://github.com/your-username/sms-phishing-firewall.git
%cd sms-phishing-firewall

!pip install -r requirements.txt -q
print("✅ Dependencies installed")
```

#### Cell 2: Configure Environment
```python
import os
from dotenv import load_dotenv

# Set your API keys (paste your actual values)
os.environ['GEMINI_API_KEY'] = 'paste-your-key-here'
os.environ['AT_USERNAME'] = 'sandbox'
os.environ['AT_API_KEY'] = 'paste-your-key-here'

print("✅ Environment configured")
```

#### Cell 3: Initialize Database
```python
from app import create_app

# Create Flask app
app = create_app()

# Initialize database
with app.app_context():
    from app.models import db
    db.create_all()
    print("✅ Database initialized")
```

#### Cell 4: Analyze Sample Messages
```python
from app.services.gemini.analyzer import GeminiAnalyzer

# Test messages
test_messages = [
    ("URGENT: Verify your account now! Click: http://bit.ly/6h3jk", True),
    ("Hi, confirming our 2pm meeting tomorrow", False),
    ("Your bank account locked. Update info: http://fake.xyz", True),
    ("Order #12345 confirmed. Thanks for shopping!", False),
]

analyzer = GeminiAnalyzer()

print("Analyzing messages:\n")
for text, is_phishing in test_messages:
    result = analyzer.analyze_message(text)
    score = min(result.get('score', 0) / 10.0, 1.0)
    prediction = "🚨 PHISHING" if score >= 0.5 else "✅ SAFE"

    print(f"{prediction} (confidence: {score:.1%})")
    print(f"Text: {text[:50]}...\n")
```

#### Cell 5: View Metrics (Optional)
```python
from app.services.evaluation.metrics import EvaluationMetrics

# If evaluation data available
try:
    metrics = EvaluationMetrics()
    print(f"Accuracy: {metrics.get_summary()['metrics']['accuracy']:.2%}")
except:
    print("Evaluation metrics not available")
```

### Step 2.3: Test the Notebook

1. Click: **"Run All"** button
2. Wait 2-3 minutes
3. Check: No errors, see analysis results
4. When ready: Click **"Share"** → **"Anyone with link"** → Copy URL

**✅ Phase 2 Complete:** Colab notebook ready to share with judges

---

## Phase 3: Cloud Run Production

### Step 3.1: GCP Prerequisites

1. **Create GCP account** if needed (get free credits)
2. **Install gcloud CLI:**
   ```bash
   # macOS
   brew install google-cloud-sdk

   # Or download: https://cloud.google.com/sdk/docs/install
   ```
3. **Verify installation:**
   ```bash
   gcloud --version
   ```

### Step 3.2: Authenticate & Create Project

```bash
# Login to Google Cloud
gcloud auth login
# Opens browser, click "Allow", paste verification code

# Create new GCP project
gcloud projects create sms-phishing-firewall

# Set as active project
gcloud config set project sms-phishing-firewall

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  compute.googleapis.com
```

### Step 3.3: Store Secrets in Secret Manager

```bash
# Create secrets for sensitive data (not in code/config)

# Gemini API Key
echo -n "your-gemini-api-key" | gcloud secrets create GEMINI_API_KEY --data-file=-

# Africa's Talking API Key
echo -n "your-at-api-key" | gcloud secrets create AT_API_KEY --data-file=-

# Africa's Talking Username
echo -n "sandbox" | gcloud secrets create AT_USERNAME --data-file=-

# Flask Secret Key (random)
echo -n "$(openssl rand -hex 32)" | gcloud secrets create FLASK_SECRET_KEY --data-file=-

# Verify they were created
gcloud secrets list
```

### Step 3.4: Verify Deployment Files

**Dockerfile** (should already exist, verify it has):

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p instance/

ENV PORT=8080
EXPOSE $PORT

CMD exec gunicorn --bind 0.0.0.0:${PORT} --workers 4 --timeout 120 run:app
```

**cloudbuild.yaml** (should already exist):
- Builds Docker image
- Pushes to Artifact Registry
- Deploys to Cloud Run
- Sets environment variables and secrets

### Step 3.5: Deploy to Cloud Run

**Option A: Using Deploy Script (Recommended)**

```bash
# Make script executable
chmod +x scripts/deploy_cloud_run.sh

# Run deployment
./scripts/deploy_cloud_run.sh sms-phishing-firewall sms-firewall us-central1

# Script will:
# 1. Check prerequisites
# 2. Build Docker image
# 3. Push to registry
# 4. Deploy to Cloud Run
# 5. Show your service URL
```

**Option B: Manual gcloud Command**

```bash
gcloud run deploy sms-firewall \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest \
  --set-secrets AT_API_KEY=AT_API_KEY:latest \
  --set-secrets AT_USERNAME=AT_USERNAME:latest \
  --set-secrets FLASK_SECRET_KEY=FLASK_SECRET_KEY:latest

# Note: First deploy takes 5-10 minutes. Grab your URL:
gcloud run services describe sms-firewall \
  --region us-central1 \
  --format='value(status.url)'
```

### Step 3.6: Configure Africa's Talking Webhook

Once Cloud Run deployment completes:

```bash
# Get your service URL
SERVICE_URL=$(gcloud run services describe sms-firewall \
  --region us-central1 \
  --format='value(status.url)')

echo "Your service URL: $SERVICE_URL"
```

Then in **Africa's Talking Dashboard:**

1. Go to: **Settings → API Callbacks**
2. Set **SMS Webhook URL:** `https://your-service-url/webhook/sms`
3. Set **USSD Webhook URL:** `https://your-service-url/webhook/ussd`
4. Click: **Save**

### Step 3.7: Test the Deployment

```bash
SERVICE_URL="https://sms-firewall-xxxxx.run.app"

# Test SMS webhook
curl -X POST $SERVICE_URL/webhook/sms \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "text=URGENT verify account http://fake.xyz&from=%2B254712345678&to=22334&id=test123"

# Should return JSON with phishing analysis
```

Check logs:

```bash
# View recent logs
gcloud run services logs read sms-firewall --region us-central1 --limit 50

# Or in GCP Console: https://console.cloud.google.com/run
```

**✅ Phase 3 Complete:** Live production endpoint ready

---

## Verification & Testing

### Repository Verification

```bash
# Verify both branches exist locally
git branch -a
# Should show:
#   main
# * production (or whichever you're on)

# Verify main is NOT cleaned (has all files)
git checkout main
git ls-files | wc -l
# Should show ~50+ files (all of them)

git ls-files | grep GETTING_STARTED
# Should show the file in git history

# Verify production is clean (removes test files from git)
git checkout production
git ls-files | wc -l
# Should show fewer files (~35-40, no tests)

git ls-files | grep test_
# Should return nothing (test files removed from production)

# Switch back to main for daily work
git checkout main
```

### Github Verification

```bash
# Check what's on remote
git branch -r
# Should show:
#   origin/main (your public repo)
# (no production remote)

# Verify main pushed correctly
git log origin/main -1
# Should show your latest commit
```

### Cloud Run Deployment Verification

```bash
# When ready to deploy, switch to production
git checkout production

# Deploy from production branch
./scripts/deploy_cloud_run.sh sms-phishing-firewall sms-firewall us-central1

# After deployment, go back to main for regular work
git checkout main
```

### What Should Be Ready

- [ ] `main` branch has all files (pushed to Github)
- [ ] `production` branch is clean (local only)
- [ ] Both branches exist locally
- [ ] Only `main` on Github remote
- [ ] Colab notebook created and shared
- [ ] Colab runs without errors
- [ ] Cloud Run service deployed (from production)
- [ ] Cloud Run URL accessible
- [ ] Webhook endpoint responds
- [ ] Africa's Talking webhook configured
- [ ] Logs show no errors

---

## Troubleshooting

### Repository Issues

| Problem | Solution |
|---------|----------|
| Main branch missing files | Don't worry, switch to `main` branch - files are there, just gitignored on production |
| Production branch missing files | Expected! Production branch has deletions. Switch to `main` to see everything. |
| Can't switch branches | You have uncommitted changes: `git stash` or `git commit -m "WIP"` first |
| Git push fails | Only push `main`: `git push origin main`. Don't push `production`. |
| .env file accidentally committed | Run: `git rm --cached .env && echo .env >> .gitignore && git commit -m "Remove .env"` |

### Colab Issues

| Problem | Solution |
|---------|----------|
| "Module not found" error | Run setup cell again: pip install -r requirements.txt |
| "API key error" | Paste correct key in environment cell |
| "Connection timeout" | Colab → Google Cloud → try again |
| Notebook won't save | Use "Save" button or Ctrl+S frequently |

### Cloud Run Issues

| Problem | Solution |
|---------|----------|
| gcloud not found | Install from https://cloud.google.com/sdk |
| Build fails | Check: `gcloud builds log [BUILD_ID]` |
| Service won't start | Check logs: `gcloud run services logs read sms-firewall` |
| Permission denied | Run: `chmod +x scripts/deploy_cloud_run.sh` |
| Project creation fails | Project name may be taken, use unique name: `gcloud projects create sms-firewall-ABC123` |

### Secrets Issues

| Problem | Solution |
|---------|----------|
| Secret not found | List all: `gcloud secrets list` |
| Wrong secret value | Update: `echo -n "new-value" \| gcloud secrets versions add SECRET_NAME --data-file=-` |
| Service can't read secret | Check IAM: Service account needs "Secret Accessor" role |

---

## File Reference

| File | Purpose | On Main | On Production |
|------|---------|---------|---------------|
| `app/` | Core Flask application | ✅ | ✅ |
| `scripts/evaluate_ai.py`, `init_db.py` | Core scripts | ✅ | ✅ |
| `Dockerfile` | Container definition | ✅ | ✅ |
| `cloudbuild.yaml` | GCP CI/CD config | ✅ | ✅ |
| `requirements.txt` | Python dependencies | ✅ | ✅ |
| `.env.example` | Template for secrets | ✅ | ✅ |
| `README.md`, `DEPLOYMENT.md` | Docs | ✅ | ✅ |
| `test_*.py` | Test files | ✅ (gitignored) | ❌ Deleted |
| `GETTING_STARTED.md` | Dev guide | ✅ | ❌ Deleted |
| `scripts/demo_*.py` | Demo scripts | ✅ | ❌ Deleted |
| `instance/` | Local database | ✅ (gitignored) | ❌ Deleted |

**Branch Strategy:**
- `main` = Full code, test files gitignored (what you push to Github & judges clone)
- `production` = Deployment-ready, test files deleted from git (local use only for Cloud Run)

---

## What to Tell Judges

> "I've deployed the SMS Phishing Firewall in two places:
>
> 1. **Google Colab** — Click this link and press 'Run All' to see live AI analysis (no setup needed)
> 2. **Google Cloud Run** — Live production endpoint analyzing real SMS in real-time
>
> The main repository branch has all the code (test files are gitignored). The production branch is used only for Cloud Run deployment with test artifacts removed.
>
> Full code and tests are available in the repository for reference."

---

## Timeline

```
Today:
  0:00 - 0:30   Phase 1: Create production branch (keep main as-is)
  0:30 - 1:00   Phase 2: Create & test Colab notebook
  1:00 - 2:00   Phase 3: Deploy to Cloud Run (from production)
  2:00 - 2:15   Verify everything works
  2:15+         Ready for judges!
```

**After deployment:**
- Main branch stays for daily development
- Switch to production branch when deploying to Cloud Run
- Only push main to Github

---

## Next Steps

1. **Daily development:**
   ```bash
   git checkout main
   # Do all your work here, commit normally
   git push origin main
   ```

2. **When ready to deploy to Cloud Run:**
   ```bash
   git checkout production
   # Deploy from this branch
   ./scripts/deploy_cloud_run.sh sms-phishing-firewall sms-firewall us-central1
   ```

3. **Share with judges:**
   - Colab link
   - Cloud Run URL
   - Github repo link (`main` branch)

4. **Monitor in production:**
   ```bash
   gcloud run services logs read sms-firewall --follow
   ```

Good luck! 🚀
