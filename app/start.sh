#!/bin/bash

# Arrêter le script si une commande échoue
set -e

echo "Attente de la base de données..."
# Optionnel : Vous pourriez ajouter ici un outil comme 'wait-for-it' 
# pour être sûr que Postgres répond avant de continuer.

echo "Exécution des migrations Alembic..."
alembic upgrade head

echo "Démarrage de l'application FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port 8000