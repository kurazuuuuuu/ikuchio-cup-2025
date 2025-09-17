#!/bin/bash

# Production deployment script
set -e

PROJECT_ID="ikuchio-cup-2025"
CLUSTER_NAME="ikuchio-prod-cluster"
REGION="asia-northeast1"
NAMESPACE="ikuchio-prod"

echo "Deploying to production..."

# Get cluster credentials
echo "Getting cluster credentials..."
gcloud container clusters get-credentials $CLUSTER_NAME --region=$REGION --project=$PROJECT_ID

# Apply production manifests
echo "Applying production manifests..."
kubectl apply -f k8s/prod/namespace.yaml
kubectl apply -f k8s/prod/backend.yaml
kubectl apply -f k8s/prod/frontend.yaml
kubectl apply -f k8s/prod/internal-lb.yaml
kubectl apply -f k8s/prod/cloudflare-tunnel.yaml

# Wait for deployments
echo "Waiting for deployments to be ready..."
kubectl rollout status deployment/ikuchio-backend -n $NAMESPACE --timeout=300s
kubectl rollout status deployment/ikuchio-frontend -n $NAMESPACE --timeout=300s
kubectl rollout status deployment/nginx-proxy -n $NAMESPACE --timeout=300s
kubectl rollout status deployment/cloudflared -n $NAMESPACE --timeout=300s

# Show status
echo "Production deployment status:"
kubectl get pods -n $NAMESPACE
kubectl get services -n $NAMESPACE

echo "Production deployment complete!"