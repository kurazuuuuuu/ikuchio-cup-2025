#!/bin/bash

# Cloud DNS setup script
set -e

PROJECT_ID="ikuchio-cup-2025"
DOMAIN="ikuchio-cup-2025-vrcat.com"
ZONE_NAME="ikuchio-zone"
STATIC_IP="34.54.141.104"

echo "Setting up Cloud DNS for $DOMAIN..."

# Create DNS zone
gcloud dns managed-zones create $ZONE_NAME \
  --description="DNS zone for ikuchio-cup-2025" \
  --dns-name=$DOMAIN \
  --visibility=public

# Add A records
gcloud dns record-sets create $DOMAIN \
  --zone=$ZONE_NAME \
  --type=A \
  --ttl=300 \
  --rrdatas=$STATIC_IP

gcloud dns record-sets create www.$DOMAIN \
  --zone=$ZONE_NAME \
  --type=A \
  --ttl=300 \
  --rrdatas=$STATIC_IP

gcloud dns record-sets create api.$DOMAIN \
  --zone=$ZONE_NAME \
  --type=A \
  --ttl=300 \
  --rrdatas=$STATIC_IP

# Get name servers
echo "DNS setup complete!"
echo "Configure your domain registrar with these name servers:"
gcloud dns managed-zones describe $ZONE_NAME --format="value(nameServers[].join(' '))"