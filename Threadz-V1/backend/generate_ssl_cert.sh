#!/bin/bash

# Generate self-signed SSL certificate for development
# DO NOT USE IN PRODUCTION

set -e

CERT_DIR="./ssl"
CERT_FILE="$CERT_DIR/localhost.crt"
KEY_FILE="$CERT_DIR/localhost.key"

echo "🔐 Generating SSL certificates for development..."

# Create SSL directory if it doesn't exist
mkdir -p "$CERT_DIR"

# Generate private key
echo "📝 Generating private key..."
openssl genrsa -out "$KEY_FILE" 2048

# Generate certificate
echo "📜 Generating certificate..."
openssl req -new -x509 -key "$KEY_FILE" -out "$CERT_FILE" -days 365 -subj "/C=IN/ST=State/L=City/O=Threadz/OU=Development/CN=localhost"

# Set appropriate permissions
chmod 600 "$KEY_FILE"
chmod 644 "$CERT_FILE"

echo "✅ SSL certificates generated successfully!"
echo "📍 Certificate: $CERT_FILE"
echo "📍 Private Key: $KEY_FILE"
echo ""
echo "⚠️  WARNING: These are self-signed certificates for development only!"
echo "   Do NOT use these in production!"
echo ""
echo "📋 To use these certificates:"
echo "   export SSL_CERT_PATH=$CERT_FILE"
echo "   export SSL_KEY_PATH=$KEY_FILE"
