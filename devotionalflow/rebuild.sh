#!/bin/bash
# Rebuild Frontend and Restart Services
# Usage: ./rebuild.sh [frontend|backend|all]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_DIR="$SCRIPT_DIR/backend"

echo "🔄 DevotionalFlow Rebuild & Restart Script"
echo "=========================================="

rebuild_frontend() {
    echo ""
    echo "📦 Rebuilding Frontend..."
    cd "$FRONTEND_DIR"
    npm run build
    echo "✅ Frontend build complete"
    
    echo ""
    echo "🔄 Reloading Nginx..."
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded"
}

restart_backend() {
    echo ""
    echo "🔄 Restarting Backend Service..."
    sudo systemctl restart kasaai-devotionalflow-backend
    sleep 2
    echo "✅ Backend service restarted"
    
    echo ""
    echo "📊 Service Status:"
    systemctl status kasaai-devotionalflow-backend --no-pager | head -10
}

check_status() {
    echo ""
    echo "📊 Checking Service Status..."
    echo ""
    echo "Backend:"
    systemctl is-active kasaai-devotionalflow-backend && echo "✅ Backend is running" || echo "❌ Backend is not running"
    echo ""
    echo "Nginx:"
    systemctl is-active nginx && echo "✅ Nginx is running" || echo "❌ Nginx is not running"
    echo ""
    echo "Frontend Build:"
    if [ -d "$FRONTEND_DIR/dist" ]; then
        echo "✅ Frontend dist directory exists"
        ls -lh "$FRONTEND_DIR/dist" | head -5
    else
        echo "❌ Frontend dist directory not found"
    fi
}

case "${1:-all}" in
    frontend)
        rebuild_frontend
        check_status
        ;;
    backend)
        restart_backend
        check_status
        ;;
    all|*)
        rebuild_frontend
        restart_backend
        check_status
        ;;
esac

echo ""
echo "✨ Rebuild and restart complete!"
echo ""

