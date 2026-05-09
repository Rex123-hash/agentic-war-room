#!/bin/bash
set -e

PROJECT_ID="${1:-agentic-war-room}"
REGION="us-central1"

echo "=== Setting active project: $PROJECT_ID ==="
gcloud config set project "$PROJECT_ID"

# ── Backend ──────────────────────────────────────────────────────────────────

echo "=== Deploying backend to Cloud Run (source build) ==="
gcloud run deploy stratify-api \
  --source . \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --set-env-vars "\
GOOGLE_CLOUD_PROJECT=${PROJECT_ID},\
GOOGLE_CLOUD_LOCATION=us-central1,\
GOOGLE_GENAI_USE_VERTEXAI=true,\
GEMINI_MODEL=gemini-2.5-flash,\
GEMINI_FALLBACK_MODEL=gemini-2.5-flash-lite,\
USE_FIRESTORE=true,\
FIRESTORE_DATABASE_ID=war-room-id,\
FIRESTORE_PROJECT_ID=${PROJECT_ID},\
ALLOYDB_DATABASE=warroom_db"

echo "=== Getting backend URL ==="
BACKEND_URL=$(gcloud run services describe stratify-api \
  --platform managed \
  --region "$REGION" \
  --format "value(status.url)")
echo "Backend: $BACKEND_URL"

# ── Frontend ─────────────────────────────────────────────────────────────────

echo "=== Building frontend with VITE_API_URL=$BACKEND_URL ==="

# Inject backend URL into the React build via a temp .env.production
echo "VITE_API_URL=$BACKEND_URL" > stratify-react/.env.production

echo "=== Deploying frontend to Cloud Run (source build) ==="
gcloud run deploy stratify-frontend \
  --source . \
  --dockerfile Dockerfile.frontend \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 8080 \
  --memory 256Mi

# Clean up temp env file
rm -f stratify-react/.env.production

echo "=== Getting frontend URL ==="
FRONTEND_URL=$(gcloud run services describe stratify-frontend \
  --platform managed \
  --region "$REGION" \
  --format "value(status.url)")

echo ""
echo "════════════════════════════════════"
echo " Deployment complete"
echo " Backend:  $BACKEND_URL"
echo " Frontend: $FRONTEND_URL"
echo "════════════════════════════════════"
