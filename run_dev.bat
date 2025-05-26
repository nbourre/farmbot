@echo off
title FarmBot Dev Server

REM Démarrer le backend dans une nouvelle fenêtre
start "Backend" cmd /k "cd backend && uvicorn app.main:app --reload"

REM Démarrer le frontend dans une autre nouvelle fenêtre
start "Frontend" cmd /k "cd frontend\farmbot-kiosk-frontend && npm run dev"
