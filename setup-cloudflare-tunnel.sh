#!/bin/bash

# Cloudflare Tunnel setup script
set -e

echo "Setting up Cloudflare Tunnel..."

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "Installing cloudflared..."
    # For macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install cloudflared
    # For Linux
    else
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
        sudo dpkg -i cloudflared-linux-amd64.deb
    fi
fi

# Login to Cloudflare (if not already logged in)
echo "Please login to Cloudflare if prompted..."
cloudflared tunnel login

# Create tunnel
TUNNEL_NAME="ikuchio-cup-2025"
echo "Creating tunnel: $TUNNEL_NAME"
cloudflared tunnel create $TUNNEL_NAME

# Get tunnel credentials
TUNNEL_ID=$(cloudflared tunnel list | grep $TUNNEL_NAME | awk '{print $1}')
echo "Tunnel ID: $TUNNEL_ID"

# Create Kubernetes secret with tunnel credentials
CREDS_FILE="$HOME/.cloudflared/$TUNNEL_ID.json"
if [ -f "$CREDS_FILE" ]; then
    echo "Creating Kubernetes secret..."
    kubectl create secret generic tunnel-credentials \
        --from-file=credentials.json="$CREDS_FILE" \
        -n ikuchio-cup-2025 \
        --dry-run=client -o yaml | kubectl apply -f -
else
    echo "Credentials file not found: $CREDS_FILE"
    echo "Please check tunnel creation and try again."
    exit 1
fi

# Apply Cloudflare Tunnel deployment
echo "Deploying Cloudflare Tunnel to GKE..."
kubectl apply -f k8s/cloudflare-tunnel.yaml

# Create DNS records
echo "Creating DNS records..."
cloudflared tunnel route dns $TUNNEL_NAME ikuchio-cup-2025.krz-tech.net
cloudflared tunnel route dns $TUNNEL_NAME api-ikuchio-cup-2025.krz-tech.net

echo "Cloudflare Tunnel setup complete!"
echo "Frontend: https://ikuchio-cup-2025.krz-tech.net"
echo "API: https://api-ikuchio-cup-2025.krz-tech.net"