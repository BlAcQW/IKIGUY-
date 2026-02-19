#!/bin/bash

# Demo Deployment API Setup Script
# This script helps configure the demo deployment API for ailabsafrica.com

echo "🚀 Setting up Demo Deployment API for ailabsafrica.com"
echo "=================================================="

# Set the API deploy key
export API_DEPLOY_KEY="sk_live_v1_Xl7dThM7cCfYl0XU6sP5o7k8yFVR6s2z9FQvh1tbTzA"

echo "✅ API Deploy Key configured:"
echo "   API_DEPLOY_KEY=sk_live_v1_Xl7dThM7cCfYl0XU6sP5o7k8yFVR6s2z9FQvh1tbTzA"

# Create demo directory if it doesn't exist
DEMO_DIR="/var/www/ailabsafrica/demos"
if [ ! -d "$DEMO_DIR" ]; then
    echo "📁 Creating demo directory: $DEMO_DIR"
    sudo mkdir -p "$DEMO_DIR"
    sudo chown www-data:www-data "$DEMO_DIR"
    sudo chmod 755 "$DEMO_DIR"
else
    echo "✅ Demo directory already exists: $DEMO_DIR"
fi

echo ""
echo "🎯 API Endpoint Ready:"
echo "   URL: https://api.ailabsafrica.com/deploy-demo"
echo "   Method: POST"
echo "   Auth: Bearer sk_live_v1_Xl7dThM7cCfYl0XU6sP5o7k8yFVR6s2z9FQvh1tbTzA"
echo ""
echo "📝 Example Usage:"
echo "   curl -X POST \"https://api.ailabsafrica.com/deploy-demo\" \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -H \"Authorization: Bearer sk_live_v1_Xl7dThM7cCfYl0XU6sP5o7k8yFVR6s2z9FQvh1tbTzA\" \\"
echo "     -d '{"
echo "       \"fileName\": \"demo-123.html\","
echo "       \"html\": \"<!DOCTYPE html><html><body><h1>Hello World</h1></body></html>\","
echo "       \"demoId\": \"demo-123\","
echo "       \"assistantName\": \"Test Bot\","
echo "       \"assistantType\": \"test\""
echo "     }'"
echo ""
echo "✅ Setup complete! The demo deployment API is ready to use."
