#!/bin/bash

# Production GKE cluster setup script
set -e

PROJECT_ID="ikuchio-cup-2025"
CLUSTER_NAME="ikuchio-prod-cluster"
REGION="asia-northeast1"
NAMESPACE="ikuchio-prod"

echo "Setting up Production GKE cluster..."

# Create production GKE Autopilot cluster
echo "Creating production cluster: $CLUSTER_NAME"
gcloud container clusters create-auto $CLUSTER_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --release-channel=regular \
    --network=default \
    --subnetwork=default \
    --cluster-version=latest

# Get cluster credentials
echo "Getting cluster credentials..."
gcloud container clusters get-credentials $CLUSTER_NAME --region=$REGION --project=$PROJECT_ID

# Create production namespace
echo "Creating production namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Create production secrets
echo "Creating production secrets..."

# Vertex AI API Key
API_KEY=$(gcloud secrets versions access latest --secret="google-vertexai-api-key")
kubectl create secret generic google-vertexai-api-key \
    --from-literal=key="$API_KEY" \
    -n $NAMESPACE \
    --dry-run=client -o yaml | kubectl apply -f -

# Cloudflare Tunnel credentials (if exists)
TUNNEL_CREDS="$HOME/.cloudflared/60c3d3b5-c367-4c43-a82e-86a74f08fa9e.json"
if [ -f "$TUNNEL_CREDS" ]; then
    kubectl create secret generic tunnel-credentials \
        --from-file=credentials.json="$TUNNEL_CREDS" \
        -n $NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
    echo "Tunnel credentials created"
else
    echo "Warning: Tunnel credentials not found at $TUNNEL_CREDS"
fi

echo "Production cluster setup complete!"
echo "Cluster: $CLUSTER_NAME"
echo "Namespace: $NAMESPACE"
echo "Region: $REGION"