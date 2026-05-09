#!/bin/bash
set -e

PROJECT_ID="agentic-war-room"
REGION="us-central1"
BACKEND_IMAGE="gcr.io/$PROJECT_ID/stratify-api"
FRONTEND_IMAGE="gcr.io/$PROJECT_ID/stratify-frontend"

echo "=== Authenticating Docker with GCR ==="
gcloud auth configure-docker --quiet

# ── Backend ──────────────────────────────────────────────────────────────────

echo "=== Building backend image ==="
docker build -t "$BACKEND_IMAGE" .

echo "=== Pushing backend image ==="
docker push "$BACKEND_IMAGE"

echo "=== Deploying backend to Cloud Run ==="
gcloud run deploy stratify-api \
  --image "$BACKEND_IMAGE" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --set-env-vars "\
GOOGLE_CLOUD_PROJECT=agentic-war-room,\
GOOGLE_CLOUD_LOCATION=us-central1,\
GOOGLE_GENAI_USE_VERTEXAI=true,\
GEMINI_MODEL=gemini-2.5-flash,\
GEMINI_FALLBACK_MODEL=gemini-2.5-flash-lite,\
USE_FIRESTORE=true,\
FIRESTORE_DATABASE_ID=war-room-id,\
FIRESTORE_PROJECT_ID=agentic-war-room,\
ALLOYDB_DATABASE=warroom_db"

# Secrets (GOOGLE_API_KEY, SLACK_BOT_TOKEN, GITHUB_TOKEN, ALLOYDB_USER, ALLOYDB_PASSWORD)
# should be added via: gcloud run services update stratify-api --set-secrets=KEY=secret-name:latest

echo "=== Getting backend URL ==="
BACKEND_URL=$(gcloud run services describe stratify-api \
  --platform managed \
  --region "$REGION" \
  --format "value(status.url)")
echo "Backend: $BACKEND_URL"

# ── Frontend ─────────────────────────────────────────────────────────────────

echo "=== Building frontend image (VITE_API_URL=$BACKEND_URL) ==="
docker build \
  --build-arg "VITE_API_URL=$BACKEND_URL" \
  -f Dockerfile.frontend \
  -t "$FRONTEND_IMAGE" \
  .

echo "=== Pushing frontend image ==="
docker push "$FRONTEND_IMAGE"

echo "=== Deploying frontend to Cloud Run ==="
gcloud run deploy stratify-frontend \
  --image "$FRONTEND_IMAGE" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 8080 \
  --memory 256Mi

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
