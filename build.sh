#!/usr/bin/env bash
set -o errexit

# Installer les dépendances
pip install -r requirements.txt

# Appliquer les migrations
python manage.py migrate --no-input

# Créer le superuser si nécessaire
python manage.py create_default_superuser


python manage.py collectstatic --no-input
