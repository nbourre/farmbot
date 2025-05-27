#!/bin/bash
set -e

echo "🔁 Lancement du backend FastAPI (uvicorn)..."
gnome-terminal -- bash -c "cd backend && source ../.venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000; exec bash"

echo "🖥️  Lancement du frontend Vue..."
gnome-terminal -- bash -c "cd frontend/farmbot-kiosk-frontend && npm run dev; exec bash"

echo "✅ Environnement de développement lancé."
