![ARIA Complete Graph](image.png)

# ARIA — Activity Report Intelligence Agent

Activity reports contain valuable information. Extracting it, connecting the dots across sources, and turning raw data into decisions takes time most teams don't have. **ARIA was built to do exactly that.**

ARIA is an AI agent specialized in activity report analysis. Its role is not to generate reports — it is to read them, understand them, and tell you what they mean. Submit your existing reports in any format (CSV, Excel, PDF, JSON, databases, APIs) and ARIA identifies the business domain, locates the relevant KPIs, cross-validates data across sources, and produces structured insights grounded in your actual data.

## What sets ARIA apart

- **Domain-adaptive analysis**: HR, finance, R&D, logistics, IT — no manual KPI configuration needed.
- **Self-extending extraction**: when a format is unsupported, ARIA can generate the missing extraction tool.
- **Context enrichment**: when domain context is insufficient, ARIA enriches its own knowledge before analysis.
- **TRIZ-driven reasoning**: identifies structural contradictions, root causes, and prioritized recommendations.
- **Action-ready outputs**: recommendations include owner, timeline, and priority level.
- **Multi-format export**: JSON, Markdown, HTML, PDF, and PowerPoint.
- **Traceability-first**: no invented gaps, explicit confidence scores, and evidence grounded in source data.

> ARIA does not write your reports. It finally makes them worth reading.

## Project architecture

This repository contains the full ARIA stack:

- `app/` → FastAPI backend, agent logic, tools, DB models, migrations, WebSocket support.
- `cra-frontend/` → React + Vite frontend.

Main backend modules:

- `app/agent/` → orchestration graph, memory, sub-agents, tool layer.
- `app/router/` and `app/service/` → API routes and business logic.
- `app/database/` + `app/alembic/` → SQLModel models and migrations.

## Tech stack

- **Backend**: FastAPI, SQLModel, Alembic, PostgreSQL.
- **AI/Orchestration**: LangGraph, LangChain, OpenAI-compatible providers, MCP tooling.
- **Frontend**: React 19, Vite, Tailwind.
- **Runtime**: Docker Compose (PostgreSQL + backend + frontend).

## Prerequisites

- Docker Desktop (with Compose)
- (Optional for local non-Docker dev) Python 3.11+ and Node.js 20+

## Configuration

Primary environment file: `app/.env`

Current Docker-compatible baseline:

```dotenv
DB_HOST=db
DB_PORT=5432
DB_NAME=hack2cash_db
DB_USER=admin
DB_PASSWORD=adminpassword
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

SECRET_KEY=<your_secret_key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=240
NVIDIA_API_KEY=<your_nvidia_api_key>
```

Generate `SECRET_KEY` with OpenSSL:

```bash
openssl rand -hex 32
```

### NVIDIA API key requirement

Using ARIA requires a valid NVIDIA API key to run model-powered analysis features. You must create and configure `NVIDIA_API_KEY` in `app/.env` before using the application. You can get your key from NVIDIA Build: https://build.nvidia.com/explore/discover

Important networking note:

- Inside Docker network, backend must use `db:5432`.
- From host machine, PostgreSQL is exposed on `localhost:5433` (because `5433:5432`).

## Run the full application (Docker)

From repository root:

```bash
docker compose -f app/docker-compose.yml up -d --build
```

Services:

- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- PostgreSQL (host access): `localhost:5433`

To stop:

```bash
docker compose -f app/docker-compose.yml down
```

## Backend local development (without Docker)

From `app/`:

```bash
pip install -r requirements.txt
fastapi dev main.py
```

## Frontend local development (without Docker)

From `cra-frontend/`:

```bash
npm install
npm run dev
```

## Database migrations (Alembic)

From `app/`:

```bash
alembic upgrade head
```

Create a migration:

```bash
alembic revision --autogenerate -m "migration message"
```

## API docs

When backend is running:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Troubleshooting

### `Could not parse SQLAlchemy URL`

Check `DATABASE_URL` format in `app/.env`.
It must look like:

```dotenv
DATABASE_URL=postgresql://user:password@host:port/database
```

### `connection to server at "db", port 5433 failed`

`5433` is the host-mapped port, not the internal container port.
For backend-to-db communication in Docker, use:

```dotenv
DB_HOST=db
DB_PORT=5432
```
