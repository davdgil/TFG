from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.config.mongo import connect_db, close_db
from src.config.settings import settings
from src.routes import customer, product, order_final, order_item


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

# Incluir todos los routers
app.include_router(customer.router)
app.include_router(product.router)
app.include_router(order_final.router)
app.include_router(order_item.router)


@app.get("/")
async def root():
    return {"message": "Chatbot API running"}


@app.get("/health")
async def health():
    return {"status": "ok"}




