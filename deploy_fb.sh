#!/bin/bash
set -e

BACKUP_DIR="/var/www_backup_$(date +%Y%m%d_%H%M%S)"
TARGET_DIR="/var/www"

echo "📐 Build du frontend Vue"
cd frontend/farmbot-kiosk-frontend
npm install
npm run build

# ✅ Vérifier si le build a bien généré index.html
if [ ! -f dist/index.html ]; then
  echo "❌ Erreur : le build Vue a échoué (index.html manquant)"
  exit 1
fi

# 🔐 Backup de l'ancien contenu de /var/www
echo "🧳 Sauvegarde de $TARGET_DIR vers $BACKUP_DIR"
sudo cp -r $TARGET_DIR "$BACKUP_DIR"

# 🚚 Copier les fichiers buildés dans /var/www
echo "🚚 Déploiement du frontend vers $TARGET_DIR"
sudo rm -rf $TARGET_DIR/*
sudo cp -r dist/* $TARGET_DIR/

# 🔁 Redémarrage du backend
echo "🔁 Redémarrage du backend FarmBot"
cd ../../
sudo systemctl restart farmbot-backend.service

echo "✅ Déploiement terminé avec succès."
