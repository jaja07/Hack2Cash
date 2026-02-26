# Hack2Cash

Backend API FastAPI avec PostgreSQL, SQLModel et migrations Alembic.

## Structure

- `app/` : code applicatif
- `app/docker-compose.yml` : services Docker (PostgreSQL + backend)
- `app/alembic/` : migrations

## Prérequis

- Python 3.11+
- Docker + Docker Compose
- (Optionnel) client PostgreSQL `psql`

## Installation locale

Depuis le dossier `app/` :

```bash
pip install -r requirements.txt
```

## Variables d'environnement

Le fichier principal est `app/.env`.

Exemple :

```dotenv
DB_HOST=localhost
DB_NAME=hack2cash_db
DB_USER=admin
DB_PASSWORD=adminpassword
DATABASE_URL=postgresql://admin:adminpassword@localhost:5433/hack2cash_db
```

## Lancer avec Docker

Depuis `app/` :

```bash
docker compose up --build
```

La base PostgreSQL est exposée sur le port `5433`.

## Migrations Alembic

Depuis `app/` :

```bash
alembic upgrade head
```

Créer une migration :

```bash
alembic revision --autogenerate -m "message"
```

## Lancer l'API en développement

Depuis `app/` :

```bash
fastapi dev main.py
```

## PostgreSQL en ligne de commande

Connexion :

```bash
psql -h localhost -p 5433 -U admin -d hack2cash_db
```

Lister les tables :

```sql
\dt
```
