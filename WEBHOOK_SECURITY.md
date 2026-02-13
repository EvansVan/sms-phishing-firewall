# Webhook Security Guide

This guide covers testing webhooks with RequestBin and implementing security measures for production.

## Table of Contents

1. [Testing with RequestBin](#testing-with-requestbin)
2. [Security Features](#security-features)
3. [Configuration](#configuration)
4. [Production Setup](#production-setup)

---

## Testing with RequestBin

### Step 1: Create a RequestBin

1. Go to [https://requestbin.com](https://requestbin.com) or [https://webhook.site](https://webhook.site)
2. Click **"Create a Request Bin"**
3. Copy the generated URL (e.g., `https://requestbin.com/r/abc123xyz`)

### Step 2: Configure in Africa's Talking Dashboard

1. Log in to [Africa's Talking Dashboard](https://account.africastalking.com)
2. Go to your **Application** settings
3. Find **SMS Callback URL** or **Webhook URL**
4. Paste your RequestBin URL: `https://requestbin.com/r/abc123xyz`
5. Save

### Step 3: Test Webhook

1. Send a test SMS to your shortcode
2. Forward a message to your shortcode
3. Go back to RequestBin and refresh
4. You'll see the POST request with all data from Africa's Talking

### Step 4: Inspect the Payload

RequestBin shows you:
- **Headers**: All HTTP headers sent by AT
- **Body**: Form data with `from`, `to`, `text`, `linkId`, `date`, `id`
- **IP Address**: The IP address of AT's servers (save this for whitelisting!)

### Step 5: Test Your Endpoint

Once you understand the payload structure:

1. **Start your Flask server:**
   ```bash
   python run.py
   ```

2. **Expose with ngrok:**
   ```bash
   ngrok http 5000
   ```

3. **Update AT dashboard** with your ngrok URL:
   ```
   https://abc123.ngrok.io/webhook/sms
   ```

4. **Send test SMS** and check your Flask logs

---

## Security Features

### 1. HMAC Signature Verification

**Purpose**: Verify that requests actually come from Africa's Talking.

**How it works:**
- Africa's Talking signs each webhook request with a secret key
- Your server verifies the signature using the same secret
- If signatures don't match, request is rejected

**Implementation:**
```python
# In app/utils/security.py
def verify_webhook_signature_from_request(secret: str) -> bool:
    # Checks headers: X-Africas-Talking-Signature, X-Webhook-Signature
    # Verifies HMAC-SHA256 signature
```

**Configuration:**
```bash
# In .env
AT_WEBHOOK_SECRET=your-secret-key-from-at-dashboard
ENABLE_WEBHOOK_SIGNATURE=true
```

**Note**: Check Africa's Talking documentation for their specific signature format. They may use:
- `X-Africas-Talking-Signature` header
- `Authorization: Bearer <token>` header
- Custom signature format

### 2. Replay Attack Prevention

**Purpose**: Prevent attackers from replaying old webhook requests.

**How it works:**
- Each webhook has a unique `id` or `linkId`
- Server tracks seen IDs in memory (use Redis in production)
- Duplicate requests are rejected

**Implementation:**
```python
# Tracks nonces (request IDs) in _seen_nonces set
# Rejects requests with duplicate IDs
```

**Configuration:**
```bash
ENABLE_REPLAY_PROTECTION=true
```

### 3. IP Whitelisting

**Purpose**: Only accept requests from Africa's Talking IP addresses.

**How it works:**
- Maintain a list of allowed IP addresses/CIDR blocks
- Check incoming request IP against whitelist
- Reject requests from unknown IPs

**Getting Africa's Talking IPs:**

1. **From RequestBin**: Check the IP address shown in RequestBin logs
2. **From AT Documentation**: Contact AT support or check their docs
3. **Common AT IP ranges** (verify with AT):
   - `54.75.249.0/24`
   - `54.75.250.0/24`

**Implementation:**
```python
# In app/utils/security.py
def ip_whitelist(allowed_ips: list):
    # Checks request.remote_addr against whitelist
    # Supports CIDR notation (e.g., 192.168.1.0/24)
```

**Configuration:**
```bash
ENABLE_IP_WHITELIST=true
AT_WEBHOOK_IP_WHITELIST=54.75.249.0/24,54.75.250.0/24
```

---

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Webhook Security
AT_WEBHOOK_SECRET=your-webhook-secret-from-at-dashboard
ENABLE_WEBHOOK_SIGNATURE=true
ENABLE_IP_WHITELIST=true
ENABLE_REPLAY_PROTECTION=true

# IP Whitelist (comma-separated or leave empty to disable)
AT_WEBHOOK_IP_WHITELIST=54.75.249.0/24,54.75.250.0/24

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=10
```

### Getting Your Webhook Secret

1. **Check Africa's Talking Dashboard:**
   - Go to Application Settings
   - Look for "Webhook Secret" or "Callback Secret"
   - If not available, contact AT support

2. **If AT doesn't provide secrets:**
   - Generate your own: `openssl rand -hex 32`
   - Configure it in AT dashboard (if they support it)
   - Or disable signature verification for now

---

## Production Setup

### Step 1: Get Africa's Talking IP Addresses

1. **Use RequestBin** to capture real webhook requests
2. **Note the IP addresses** from RequestBin logs
3. **Contact AT support** to confirm their IP ranges
4. **Update whitelist** in production config

### Step 2: Configure Webhook Secret

1. **Get secret from AT dashboard** or generate one
2. **Set in production environment** (use Secret Manager in GCP)
3. **Never commit secrets** to git

### Step 3: Enable All Security Features

```bash
# Production .env
ENABLE_WEBHOOK_SIGNATURE=true
ENABLE_IP_WHITELIST=true
ENABLE_REPLAY_PROTECTION=true
AT_WEBHOOK_SECRET=<from-secret-manager>
AT_WEBHOOK_IP_WHITELIST=<verified-ip-ranges>
```

### Step 4: Use Redis for Replay Protection

For production, replace in-memory storage with Redis:

```python
# In app/utils/security.py
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def check_replay(nonce_hash: str) -> bool:
    if redis_client.exists(f"nonce:{nonce_hash}"):
        return True
    redis_client.setex(f"nonce:{nonce_hash}", 300, "1")  # 5 min TTL
    return False
```

---

## Testing Security Features

### Test 1: Signature Verification

```bash
# Test with invalid signature
curl -X POST http://localhost:5000/webhook/sms \
  -H "X-Webhook-Signature: invalid-signature" \
  -d "from=+254712345678&text=test"

# Should return: 401 Unauthorized
```

### Test 2: IP Whitelist

```bash
# Test from non-whitelisted IP (use VPN or different server)
curl -X POST http://your-domain.com/webhook/sms \
  -d "from=+254712345678&text=test"

# Should return: 403 Forbidden
```

### Test 3: Replay Attack

```bash
# Send same request twice
curl -X POST http://localhost:5000/webhook/sms \
  -d "id=test-123&from=+254712345678&text=test"

# First: 200 OK
# Second: 409 Conflict (duplicate)
```

---

## Troubleshooting

### Issue: "Invalid signature" errors

**Solution:**
1. Check `AT_WEBHOOK_SECRET` is correct
2. Verify AT's signature format (check their docs)
3. Temporarily disable: `ENABLE_WEBHOOK_SIGNATURE=false` (for testing only!)

### Issue: "Unauthorized IP" errors

**Solution:**
1. Check RequestBin to see actual AT IPs
2. Update `AT_WEBHOOK_IP_WHITELIST` with correct IPs
3. Temporarily disable: `ENABLE_IP_WHITELIST=false` (for testing only!)

### Issue: "Duplicate request" errors

**Solution:**
1. This is normal - means replay protection is working
2. If legitimate requests are being rejected, check nonce storage
3. For production, use Redis instead of in-memory storage

---

## Best Practices

1. **Always test with RequestBin first** to understand payload structure
2. **Enable security features gradually** - test each one individually
3. **Use Redis in production** for replay protection (not in-memory)
4. **Monitor logs** for security violations
5. **Keep IP whitelist updated** - AT may change their IPs
6. **Rotate webhook secrets** periodically
7. **Never disable security in production** without good reason

---

## Additional Resources

- [RequestBin Documentation](https://requestbin.com/docs)
- [Webhook Security Best Practices](https://webhooks.fyi/best-practices/security)
- [Africa's Talking Support](https://help.africastalking.com)

