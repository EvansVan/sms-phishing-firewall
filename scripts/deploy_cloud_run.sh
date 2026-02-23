#!/bin/bash
# Cloud Run Deployment Script for SMS Phishing Firewall
#
# Usage:
#   ./scripts/deploy_cloud_run.sh [PROJECT_ID] [SERVICE_NAME] [REGION]
#
# Example:
#   ./scripts/deploy_cloud_run.sh my-gcp-project sms-firewall us-central1

set -e

# Configuration
PROJECT_ID="${1:-sms-phishing-firewall}"
SERVICE_NAME="${2:-sms-firewall}"
REGION="${3:-us-central1}"
DOCKERFILE="${4:-Dockerfile}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Main deployment
print_header "SMS PHISHING FIREWALL - CLOUD RUN DEPLOYMENT"

echo "Configuration:"
echo "  Project ID:   $PROJECT_ID"
echo "  Service:      $SERVICE_NAME"
echo "  Region:       $REGION"
echo "  Dockerfile:   $DOCKERFILE"

# Check prerequisites
print_header "Checking Prerequisites"

if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI not found. Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi
print_success "gcloud CLI found"

if ! command -v docker &> /dev/null; then
    print_warning "Docker not found locally. Cloud Build will be used instead."
else
    print_success "Docker found"
fi

if [ ! -f "$DOCKERFILE" ]; then
    print_error "Dockerfile not found at: $DOCKERFILE"
    exit 1
fi
print_success "Dockerfile found"

# Set GCP project
print_header "Configuring GCP Project"

echo "Setting active project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID
print_success "Project set"

# Check if project exists
if ! gcloud projects describe $PROJECT_ID &> /dev/null; then
    print_warning "Project $PROJECT_ID doesn't exist. Creating..."
    gcloud projects create $PROJECT_ID
    print_success "Project created"
fi

# Enable required APIs
print_header "Enabling Required APIs"

APIS=(
    "run.googleapis.com"
    "artifactregistry.googleapis.com"
    "cloudbuild.googleapis.com"
    "compute.googleapis.com"
)

for api in "${APIS[@]}"; do
    echo -n "Enabling $api... "
    gcloud services enable $api --quiet 2>/dev/null
    print_success "Done"
done

# Check secrets
print_header "Verifying Required Secrets"

REQUIRED_SECRETS=(
    "GEMINI_API_KEY"
    "AT_API_KEY"
    "AT_USERNAME"
    "FLASK_SECRET_KEY"
)

for secret in "${REQUIRED_SECRETS[@]}"; do
    if gcloud secrets describe $secret &> /dev/null; then
        print_success "$secret exists"
    else
        print_warning "$secret not found in Secret Manager"
        read -p "Enter value for $secret: " secret_value
        echo -n "$secret_value" | gcloud secrets create $secret --data-file=- 2>/dev/null
        print_success "Created $secret"
    fi
done

# Build and deploy
print_header "Building and Deploying"

if [ -f "cloudbuild.yaml" ]; then
    print_info "Using Cloud Build (cloudbuild.yaml)"
    echo "Submitting build..."
    gcloud builds submit \
        --config=cloudbuild.yaml \
        --substitutions=_SERVICE_NAME=$SERVICE_NAME,_REGION=$REGION
else
    print_info "Using gcloud run deploy directly"
    gcloud run deploy $SERVICE_NAME \
        --source . \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --memory 1Gi \
        --cpu 1 \
        --timeout 120 \
        --max-instances 100 \
        --set-env-vars="FLASK_ENV=production" \
        --set-secrets=GEMINI_API_KEY=GEMINI_API_KEY:latest \
        --set-secrets=AT_API_KEY=AT_API_KEY:latest \
        --set-secrets=AT_USERNAME=AT_USERNAME:latest \
        --set-secrets=FLASK_SECRET_KEY=FLASK_SECRET_KEY:latest \
        --quiet
fi

print_success "Deployment submitted"

# Get service URL
print_header "Getting Service URL"

echo "Waiting for service to be ready..."
sleep 10

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --format='value(status.url)' \
    --quiet)

if [ -z "$SERVICE_URL" ]; then
    print_error "Could not retrieve service URL"
    exit 1
fi

print_success "Service deployed!"

# Output summary
print_header "Deployment Summary"

echo -e "Service URL:\n  ${GREEN}$SERVICE_URL${NC}\n"
echo "Next steps:"
echo "  1. Configure webhook in Africa's Talking dashboard:"
echo "     SMS:  $SERVICE_URL/webhook/sms"
echo "     USSD: $SERVICE_URL/webhook/ussd"
echo ""
echo "  2. Test the webhook:"
echo "     curl -X POST $SERVICE_URL/webhook/sms \\"
echo "       -d 'text=Hello&from=%2B254712345678&to=22334'"
echo ""
echo "  3. View logs:"
echo "     gcloud logging read \"resource.type=cloud_run_revision\" --limit 50"
echo ""
echo "  4. Monitor:"
echo "     gcloud run services describe $SERVICE_NAME --region $REGION"

# Save URL to file
echo "$SERVICE_URL" > .cloud-run-url
print_success "Service URL saved to .cloud-run-url"

print_header "✅ Deployment Complete!"
