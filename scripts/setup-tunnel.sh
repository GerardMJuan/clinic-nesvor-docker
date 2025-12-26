#!/bin/bash
# Cloudflare Tunnel Setup Script for Fetal MRI Reconstruction
# This script helps configure secure remote access

set -e

echo "=========================================="
echo "Fetal MRI - Cloudflare Tunnel Setup"
echo "=========================================="
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "Installing cloudflared..."
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
    chmod +x /usr/local/bin/cloudflared
    echo "✓ cloudflared installed"
else
    echo "✓ cloudflared already installed"
fi

echo ""
echo "Step 1: Login to Cloudflare"
echo "---------------------------"
echo "This will open a browser window. Log in and authorize."
read -p "Press Enter to continue..."
cloudflared tunnel login
echo "✓ Logged in"

echo ""
echo "Step 2: Create Tunnel"
echo "---------------------"
read -p "Enter a name for your tunnel (e.g., fetal-mri): " TUNNEL_NAME
TUNNEL_NAME=${TUNNEL_NAME:-fetal-mri}

# Check if tunnel already exists
if cloudflared tunnel list | grep -q "$TUNNEL_NAME"; then
    echo "Tunnel '$TUNNEL_NAME' already exists"
    TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
else
    cloudflared tunnel create "$TUNNEL_NAME"
    TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
fi
echo "✓ Tunnel ID: $TUNNEL_ID"

echo ""
echo "Step 3: Configure Domain"
echo "------------------------"
read -p "Enter your full domain (e.g., mri.yourclinic.com): " DOMAIN

# Create config file
CONFIG_DIR="$HOME/.cloudflared"
mkdir -p "$CONFIG_DIR"

cat > "$CONFIG_DIR/config.yml" << EOF
tunnel: $TUNNEL_ID
credentials-file: $CONFIG_DIR/$TUNNEL_ID.json

ingress:
  - hostname: $DOMAIN
    service: http://localhost:8501
  - service: http_status:404
EOF

echo "✓ Config created at $CONFIG_DIR/config.yml"

echo ""
echo "Step 4: Create DNS Record"
echo "-------------------------"
echo "Adding DNS record for $DOMAIN..."
cloudflared tunnel route dns "$TUNNEL_NAME" "$DOMAIN" || {
    echo "Note: DNS record may already exist or domain not in Cloudflare"
    echo "You may need to add it manually in Cloudflare Dashboard"
}

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Start the web app:"
echo "   docker-compose -f docker-compose.webapp.yml up -d"
echo ""
echo "2. Start the tunnel:"
echo "   cloudflared tunnel run $TUNNEL_NAME"
echo ""
echo "3. (Optional) Install as service for auto-start:"
echo "   sudo cloudflared service install"
echo "   sudo systemctl enable cloudflared"
echo "   sudo systemctl start cloudflared"
echo ""
echo "4. Add login protection:"
echo "   - Go to: https://one.dash.cloudflare.com"
echo "   - Navigate to: Access → Applications → Add Application"
echo "   - Add your domain: $DOMAIN"
echo "   - Create a policy with allowed email addresses"
echo ""
echo "Your app will be available at: https://$DOMAIN"
echo ""
