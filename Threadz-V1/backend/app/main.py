import contextlib
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import engine, Base
from . import auth, designs, products, orders

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup tables on startup (since we aren't using Alembic actively right now for SQLite local dev)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Teardown logic if any

app = FastAPI(title="Threadz Custom Fashion Platform", version="1.0", lifespan=lifespan)

# Add CORS with security best practices
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(designs.router)
app.include_router(products.router)
app.include_router(orders.router)

import os
os.makedirs("uploads/designs", exist_ok=True)
app.mount("/api/v1/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
