from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router import user_router
from router import agent_router
from router import chat_router
from router import websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application démarrée. Les migrations sont gérées par Alembic.")
    yield
    print("Fermeture de l'application...")


app = FastAPI(
    title="Hack2Cash API",
    description="Système agentique pour le pilotage de la rentabilité des entreprises à partir des comptes rendus d'activité",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router.router, prefix="/api")
app.include_router(agent_router.router, prefix="/api")
app.include_router(chat_router.router, prefix="/api")
app.include_router(websocket.router, prefix="/api")


@app.get("/", tags=["Health"])
async def root():
    return {"message": "API is running", "status": "ok"}
