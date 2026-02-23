# Git Branch Strategy: Production vs Development

## Overview

```
main          ← Production-ready (clean, only essential files)
  ↓
dev           ← Development (all files: tests, docs, scripts)
  ↓
your-feature  ← (optional: feature branches)
```

---

## Step-by-Step: Create Production Branch

### Step 1: Check Current Status

```bash
cd ~/Desktop/AT\ \&\ Gemini/sms-phishing-firewall

# Check current branch
git branch -a

# Check status
git status
```

Expected output: You're on `main` branch, everything committed.

### Step 2: Backup Current Branch as `dev`

```bash
# Create dev branch from current main
git branch dev

# Verify it was created
git branch -a
# Output should show:
#   dev
# * main
```

### Step 3: Clean `main` Branch for Production

While on `main`, remove dev/test files:

```bash
# Switch to main (if not already)
git checkout main

# Remove test files
rm -f test_*.py test_*.md *_test.py

# Remove dev documentation
rm -f GETTING_STARTED.md QUICK_START.md WEBHOOK_SECURITY.md

# Remove dev scripts
rm -f scripts/demo_evaluation.py scripts/seed_data.py create_test_campaign.py

# Optionally remove database artifacts (can regenerate)
rm -rf instance/

# Stage deletions
git add -A

# Commit cleanup
git commit -m "Production: Remove dev files, test files, and documentation

- Remove test_*.py, test_*.md, *_test.py (all test files)
- Remove GETTING_STARTED.md, QUICK_START.md, WEBHOOK_SECURITY.md
- Remove dev-only scripts (demo_evaluation.py, seed_data.py)
- Remove create_test_campaign.py
- Clean up database artifacts (instance/ directory)

This branch (main) contains only production-ready code for Cloud Run deployment."
```

### Step 4: Verify `main` is Clean

```bash
# List files in repo
ls -la

# Should NOT have:
# - test files
# - GETTING_STARTED.md, QUICK_START.md, WEBHOOK_SECURITY.md
# - test_evaluation.md or test files

# Should HAVE:
# - app/ (core app)
# - scripts/evaluate_ai.py, init_db.py
# - run.py, requirements.txt
# - Dockerfile, cloudbuild.yaml
# - README*.md, DEPLOYMENT*.md, COLAB*.md, EVALUATION*.md
# - .env.example, .gitignore

# Verify with git
git ls-files | head -20
```

### Step 5: Push Both Branches to Github

```bash
# Push main (production)
git push origin main

# Push dev (with everything)
git push -u origin dev

# Verify both exist on Github
git branch -r
# Output should show:
#   origin/HEAD -> origin/main
#   origin/dev
#   origin/main
```

### Step 6: Set Default Branch in Github (Optional but Recommended)

1. Go to your Github repo: https://github.com/your-username/sms-phishing-firewall
2. Click **Settings** (top menu)
3. Click **Branches** (left sidebar)
4. Under "Default branch", select **main**
5. Click **Update** (if prompted)

This ensures new clones default to production-clean `main` branch.

---

## Verify Your Branch Setup

```bash
# Check both branches exist locally
git branch -a

# Check both branches exist on remote
git branch -r

# View commits on main (should show cleanup)
git log --oneline main | head -5

# View commits on dev (should have all history)
git log --oneline dev | head -5

# View what files are on each branch
echo "=== FILES ON MAIN ==="
git ls-files --stage | wc -l

echo "=== FILES ON DEV ==="
git checkout dev
git ls-files --stage | wc -l

# Switch back to main
git checkout main
```

---

## Understanding Your Branches

### `main` Branch (Production)
```
Files: ONLY essentials for Cloud Run deployment
  ✅ app/
  ✅ run.py
  ✅ requirements.txt
  ✅ Dockerfile
  ✅ scripts/evaluate_ai.py, init_db.py
  ✅ README*.md, DEPLOYMENT*.md, EVALUATION*.md
  ✅ data/evaluation_dataset.csv
  ✅ cloudbuild.yaml
  ❌ test_*.py, test_*.md
  ❌ GETTING_STARTED.md, QUICK_START.md
  ❌ scripts/demo_evaluation.py, seed_data.py

Size: Minimal (optimal for Git clone during deployment)
Use for: Cloud Run deployment, production submission
```

### `dev` Branch (Development)
```
Files: Everything (original state)
  ✅ All of main, PLUS:
  ✅ test_*.py (all test files)
  ✅ test_*.md (test documentation)
  ✅ GETTING_STARTED.md, QUICK_START.md, WEBHOOK_SECURITY.md
  ✅ scripts/demo_evaluation.py, seed_data.py
  ✅ create_test_campaign.py
  ✅ instance/ (database artifacts)
  ✅ migrations/ (if applicable)

Size: Full (includes everything)
Use for: Local development, testing, experiments
```

---

## Working with Both Branches

### Clone for Production
```bash
# Default clones main (production)
git clone https://github.com/your-username/sms-phishing-firewall.git
cd sms-phishing-firewall
# You're now on main with clean production files
```

### Clone for Development
```bash
# Clone then switch to dev
git clone https://github.com/your-username/sms-phishing-firewall.git
cd sms-phishing-firewall
git checkout dev
# You're now on dev with all files including tests
```

### Switch Between Branches
```bash
# When on main (production)
git checkout dev      # Switch to development

# When on dev (development)
git checkout main     # Switch to production

# See current branch
git branch
# Output shows current with *
```

---

## Workflow for Future Development

### Add New Feature

```bash
# Start on dev branch (where all dev files are)
git checkout dev

# Create feature branch from dev
git checkout -b feature/new-feature dev

# Make changes, test (can use test_*.py files)
# ...

# Commit
git add -A
git commit -m "Feature: Add new feature"

# Push
git push origin feature/new-feature

# Create Pull Request on Github (feature → dev)
```

### Merge to Production

```bash
# On feature branch, after review:
git checkout dev
git pull origin dev
git merge feature/new-feature

# Test thoroughly on dev

# Switch to main
git checkout main
git pull origin main

# Merge from dev to main
git merge dev

# Push
git push origin main

# Clean up feature branch
git branch -d feature/new-feature
git push origin --delete feature/new-feature
```

---

## For Competition Submission

### What to Submit

1. **Repository URL:**
   ```
   https://github.com/your-username/sms-phishing-firewall
   ```

2. **Judges will see:**
   - Default branch is `main` (production-clean)
   - Clean, minimal, deployment-ready
   - Professional appearance

3. **If judges want to see everything:**
   ```bash
   git checkout dev
   # Now they see all test files, documentation, dev scripts
   ```

---

## Verify Everything Works

```bash
# From main branch, verify deployment still works
git checkout main

# Test Docker build works
docker build -t sms-firewall .

# Test pip install works
pip install -r requirements.txt

# Test app runs
python run.py

# Should start Flask server without errors
# ✅ If this works, main branch is production-ready
```

---

## Branch Status Check

Run this to see the full picture:

```bash
#!/bin/bash
echo "=== BRANCH STATUS ==="
git branch -a
echo ""

echo "=== CURRENT BRANCH ==="
git branch --show-current
echo ""

echo "=== MAIN BRANCH FILES ==="
git checkout main 2>/dev/null
echo "Total files: $(git ls-files | wc -l)"
echo "Has test files: $(git ls-files | grep -c 'test_' || echo '0')"
echo ""

echo "=== DEV BRANCH FILES ==="
git checkout dev 2>/dev/null
echo "Total files: $(git ls-files | wc -l)"
echo "Has test files: $(git ls-files | grep -c 'test_' || echo '0')"
echo ""

echo "=== SWITCH BACK TO MAIN ==="
git checkout main 2>/dev/null
git branch --show-current
```

---

## How to Execute This Plan Right Now

```bash
# 1. Navigate to repo
cd ~/Desktop/AT\ \&\ Gemini/sms-phishing-firewall

# 2. Create dev branch (backup of current state)
git branch dev

# 3. Make sure you're on main
git checkout main

# 4. Remove dev files
rm -f test_*.py test_*.md *_test.py
rm -f GETTING_STARTED.md QUICK_START.md WEBHOOK_SECURITY.md
rm -f scripts/demo_evaluation.py scripts/seed_data.py create_test_campaign.py
rm -rf instance/

# 5. Commit cleanup
git add -A
git commit -m "Production: Remove dev/test files for Cloud Run deployment"

# 6. Push both branches
git push origin main
git push -u origin dev

# 7. Verify
git branch -r
git log --oneline -5
```

---

## Benefits of This Approach

✅ **Production-clean** — `main` has only what's needed
✅ **Development-friendly** — `dev` has everything for testing
✅ **Git-native** — Uses standard Git workflow
✅ **Easy to switch** — `git checkout main` vs `git checkout dev`
✅ **Safe** — Nothing is deleted, just moved to different branch
✅ **Professional** — Judges see clean production code
✅ **Future-proof** — Easy to add feature branches later

---

## FAQ

### Q: Can I recover deleted files?
**A:** Yes! They're on the `dev` branch. Switch with `git checkout dev`

### Q: What if I need a test file on main?
**A:** Add it as needed, or merge that specific file from dev: `git checkout dev -- test_file.py`

### Q: Which branch for Cloud Run?
**A:** `main` (production-clean). Deployment script uses default branch.

### Q: Can I delete dev after deployment?
**A:** Not recommended. Keep it for:
  - Rollback if issues
  - Reference for complete history
  - Future development

### Q: How do judges access everything?
**A:** Send them repo link and mention: "Full repo at main (production), full code at dev branch"

---

## Ready to Execute?

Run these commands:

```bash
cd ~/Desktop/AT\ \&\ Gemini/sms-phishing-firewall

# Verify current state
git status
git branch

# Create dev branch
git branch dev

# Clean main
git checkout main
rm -f test_*.py test_*.md *_test.py GETTING_STARTED.md QUICK_START.md WEBHOOK_SECURITY.md scripts/demo_evaluation.py scripts/seed_data.py create_test_campaign.py
rm -rf instance/

# Commit
git add -A
git commit -m "Production: Remove dev/test files for Cloud Run deployment"

# Push
git push origin main
git push -u origin dev

# Verify
git branch -r
```

Done! `main` is now production-ready, `dev` has everything.
