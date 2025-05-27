#!/bin/bash
set -e

# Dossier racine
ROOT_DIR=$(pwd)

# Lancer le backend dans un nouvel onglet
osascript <<EOF
tell application "Terminal"
    activate
    do script "cd \"$ROOT_DIR\"; source .venv/bin/activate; cd backend; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
end tell
EOF

# Lancer le frontend dans un autre onglet
osascript <<EOF
tell application "Terminal"
    activate
    do script "cd \"$ROOT_DIR/frontend/farmbot-kiosk-frontend\"; npm run dev"
end tell
EOF

echo "✅ Backend et frontend lancés dans Terminal.app"
