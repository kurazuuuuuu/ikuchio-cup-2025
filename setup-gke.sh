#!/bin/bash

# GKE cluster setup script
set -e

PROJECT_ID="ikuchio-cup-2025"
CLUSTER_NAME="autopilot-cluster-1"
REGION="asia-northeast1"

echo "Setting up GKE cluster for ikuchio-cup-2025..."

# Create GKE cluster
gcloud container clusters create $CLUSTER_NAME \
  --region=$REGION \
  --num-nodes=2 \
  --machine-type=e2-standard-2 \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=5 \
  --enable-autorepair \
  --enable-autoupgrade \
  --workload-pool=$PROJECT_ID.svc.id.goog \
  --enable-ip-alias \
  --network=default \
  --subnetwork=default

# Get credentials
gcloud container clusters get-credentials $CLUSTER_NAME --region=$REGION

# Create static IP
gcloud compute addresses create ikuchio-ip --global

# Enable Workload Identity
gcloud iam service-accounts add-iam-policy-binding \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:$PROJECT_ID.svc.id.goog[ikuchio-cup-2025/ikuchio-gke-sa]" \
  ikuchio-cicd@$PROJECT_ID.iam.gserviceaccount.com

echo "GKE cluster setup complete!"
echo "Static IP: $(gcloud compute addresses describe ikuchio-ip --global --format='value(address)')"