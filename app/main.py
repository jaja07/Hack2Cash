from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router import user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # En phase de développement avec Alembic, on ne crée plus les tables ici.
    # On laisse Alembic gérer les migrations depuis le terminal.
    print("Application démarrée. Les migrations sont gérées par Alembic.")
    yield
    print("Fermeture de l'application...")

app = FastAPI(
    title="Hack2Cash API",
    description="Système agentique pour le pilotage de la rentabilité des entreprises à partir des comptes rendus d'activité",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration du CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router.router)

@app.get("/", tags=["Health"])
async def root():
    return {"message": "API is running", "status": "ok"}