# Google Colab Deployment Guide

## What is Google Colab?

A free, shareable Python notebook environment from Google. Perfect for:
- 📊 Live demos for judges (no setup needed)
- 🚀 Interactive testing
- 💡 Educational walkthroughs
- 🔗 Shareable link (judges can click and run)

---

## Step-by-Step: Create Colab Notebook

### Step 1: Go to Google Colab

Open: https://colab.research.google.com

Click: **"New notebook"**

### Step 2: Create Cell 1 - Clone Repository

Click **"+ Code"** and paste:

```python
# Clone the SMS Phishing Firewall repository
!git clone https://github.com/your-username/sms-phishing-firewall.git
%cd sms-phishing-firewall

print("✅ Repository cloned")
```

Run the cell (Shift+Enter)

### Step 3: Create Cell 2 - Install Dependencies

Click **"+ Code"** and paste:

```python
# Install all required packages silently
!pip install -r requirements.txt -q

print("✅ All dependencies installed successfully")
```

Run the cell (this takes 1-2 minutes)

### Step 4: Create Cell 3 - Set API Keys

Click **"+ Code"** and paste:

```python
import os
from google.colab import userdata

# Get API keys from Colab Secrets (secure way)
# First time: you'll be prompted to enter keys
# After: they're stored securely in your Colab account

try:
    # Load from environment
    GEMINI_API_KEY = userdata.get('GEMINI_API_KEY')
    AT_API_KEY = userdata.get('AT_API_KEY')
    AT_USERNAME = userdata.get('AT_USERNAME')
except:
    # Fallback: paste directly (less secure)
    GEMINI_API_KEY = input("Enter GEMINI_API_KEY: ")
    AT_API_KEY = input("Enter AT_API_KEY: ")
    AT_USERNAME = input("Enter AT_USERNAME (usually 'sandbox' for testing): ")

# Set environment variables
os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY
os.environ['AT_API_KEY'] = AT_API_KEY
os.environ['AT_USERNAME'] = AT_USERNAME
os.environ['DATABASE_URL'] = 'sqlite:///firewall.db'
os.environ['FLASK_ENV'] = 'development'

print("✅ API keys configured")
```

Run the cell

### Step 5: Create Cell 4 - Initialize App & Database

Click **"+ Code"** and paste:

```python
from dotenv import load_dotenv
import sys

# Load environment
load_dotenv()

# Import app components
from app import create_app
from app.models import db

# Create Flask app
app = create_app()

# Initialize database
with app.app_context():
    db.create_all()
    print("✅ Database initialized")
    print(f"✅ Flask app ready")
```

Run the cell

### Step 6: Create Cell 5 - Quick Evaluation Demo

Click **"+ Code"** and paste:

```python
from app.services.gemini.analyzer import GeminiAnalyzer
from app.services.evaluation.metrics import EvaluationMetrics

# Test messages
test_messages = [
    ("Hello! Your account has been suspended. Click here to verify: http://bit.ly/6h3jk", True),
    ("Hi Sarah, this is John from HR. Just confirming our meeting tomorrow at 2pm.", False),
    ("URGENT: Your bank account will be closed. Update payment info now: http://bank-verify.xyz", True),
    ("Congratulations! You've won $1,000 voucher. Claim now: http://prize.click/abc123", True),
    ("Mom, can you send me $50? Having car trouble.", False),
]

metrics = EvaluationMetrics()

print("🔍 Analyzing messages...\n")
print("="*70)

with app.app_context():
    analyzer = GeminiAnalyzer()

    for idx, (text, is_phishing) in enumerate(test_messages, 1):
        try:
            result = analyzer.analyze_message(text)
            score = min(result.get('score', 0) / 10.0, 1.0)
            predicted = "🚨 PHISHING" if score >= 0.5 else "✅ SAFE"

            print(f"\n{idx}. {predicted}")
            print(f"   Confidence: {score:.1%}")
            print(f"   Message: {text[:60]}...")

            metrics.add_prediction(
                actual_label=is_phishing,
                predicted_score=score,
                message_text=text,
                category="test"
            )
        except Exception as e:
            print(f"\n{idx}. ❌ Error: {e}")

print("\n" + "="*70)
```

Run the cell (this takes 1-2 minutes as it calls Gemini API)

### Step 7: Create Cell 6 - Show Results

Click **"+ Code"** and paste:

```python
# Get and display metrics
summary = metrics.get_summary()
metrics_data = summary['metrics']

print("\n" + "="*70)
print("📊 EVALUATION RESULTS")
print("="*70 + "\n")

print(f"Total Messages Analyzed: {summary['total_predictions']}")
print(f"Phishing: {summary['phishing_count']} | Legitimate: {summary['legitimate_count']}\n")

print("Metrics:")
print(f"  F1-Score:    {metrics_data['f1_score']:.4f}  ← Best overall metric")
print(f"  Accuracy:    {metrics_data['accuracy']:.2%}")
print(f"  Precision:   {metrics_data['precision']:.2%}  (Alert quality)")
print(f"  Recall:      {metrics_data['recall']:.2%}  (Threat coverage)")
print(f"  ROC-AUC:     {metrics_data['roc_auc']:.4f}  (Model quality)")
print(f"  False Pos:   {metrics_data['false_positive_rate']:.2%}  (User experience)")

# Performance grade
f1 = metrics_data['f1_score']
if f1 >= 0.90:
    grade = "🟢 A+ (Excellent)"
elif f1 >= 0.80:
    grade = "🟢 A (Very Good)"
elif f1 >= 0.70:
    grade = "🟡 B (Good)"
else:
    grade = "🔴 C (Needs Improvement)"

print(f"\nPerformance Grade: {grade}")
print("\n" + "="*70)
```

Run the cell

### Step 8: Create Cell 7 - Interactive Testing

Click **"+ Code"** and paste:

```python
# Test a custom message
custom_message = "Limited time offer! Get free iPhone now: http://fake-offer.xyz"

print(f"\n🧪 Testing custom message:")
print(f"   \"{custom_message}\"\n")

with app.app_context():
    result = analyzer.analyze_message(custom_message)
    score = min(result.get('score', 0) / 10.0, 1.0)
    verdict = "🚨 PHISHING" if score >= 0.5 else "✅ SAFE"

    print(f"Verdict:     {verdict}")
    print(f"Confidence:  {score:.1%}")
    print(f"Raw Score:   {result.get('score', 0)}/10")
    print(f"\nAnalysis:\n{result.get('summary', 'No summary available')}")
```

Run the cell

---

## Step 9: Share with Judges

### Save the Notebook

Click: **File** → **Save** → Name it: `"SMS Phishing Firewall Demo"`

### Share the Link

Click: **Share** button (top right)
- Change to: **"Anyone with the link"**
- Click **Copy link**
- Send to judges!

### Judges Can:
1. Click the link (no login needed if set to "Anyone")
2. Click **"Run All"** to execute everything
3. See live results in minutes
4. Try their own test messages (modify Cell 8)

---

## Alternative: Quickstart Colab (Minimal)

If you only want judges to see results quickly, use this shorter notebook:

### Cell 1: Setup
```python
!git clone https://github.com/your-username/sms-phishing-firewall.git
%cd sms-phishing-firewall
!pip install -r requirements.txt -q
print("✅ Ready")
```

### Cell 2: Demo
```python
import os
os.environ['GEMINI_API_KEY'] = 'your-key-here'  # paste your key

from app import create_app
from app.services.gemini.analyzer import GeminiAnalyzer

app = create_app()

with app.app_context():
    analyzer = GeminiAnalyzer()

    result = analyzer.analyze_message(
        "Your account has been suspended. Verify here: http://fake.xyz"
    )

    score = result.get('score', 0) / 10.0
    print(f"Score: {score:.1%} - {'🚨 PHISHING' if score >= 0.5 else '✅ SAFE'}")
```

---

## Colab Advantages for Competition

✅ **No Setup Needed** — Judges click link and run
✅ **Free** — No GCP credits needed (Colab is free)
✅ **Shareable** — Link works for anyone
✅ **Live Demo** — Shows AI working in real-time
✅ **Interactive** — Judges can modify and test
✅ **Professional** — Looks polished and organized

---

## Troubleshooting in Colab

| Problem | Solution |
|---------|----------|
| "Module not found" | Run Cell 2 again (pip install) |
| "API key invalid" | Paste correct key from `.env` |
| "Connection error" | Check internet connection |
| "Timeout" | Gemini API can be slow, wait 30s |
| "Can't install package" | Try: `!pip install --upgrade pip` first |

---

## Next: Deploy to Cloud Run

After testing in Colab, move to production with Cloud Run:
See **DEPLOYMENT.md** → [Phase 3: Cloud Run Production](DEPLOYMENT.md#phase-3-cloud-run-production)

---

**Share Colab with judges:** [Your Colab Link Here]
**Expected run time:** 3-5 minutes for full evaluation
