FROM python:3.11-slim

WORKDIR /app/

# Installation des dépendances système nécessaires pour psycopg2 (Postgres)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Rendre le script de démarrage exécutable
RUN chmod +x start.sh

EXPOSE 8000

# Lancement via le script de démarrage
CMD ["/bin/bash", "start.sh"]