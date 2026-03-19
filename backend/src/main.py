from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.config.mongo import connect_db, close_db
from src.config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: conectar a MongoDB
    await connect_db()
    yield
    # Shutdown: cerrar conexión
    await close_db()


app = FastAPI(
    title="Chatbot API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS para frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambiar en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Chatbot API running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
