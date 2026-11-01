
from fastapi import FastAPI
from app.routes.auth import router as auth_router

from app.routes.health import router as health_router

app = FastAPI(
    title="NTIRO API",
    description="National Threat & Risk Intelligence Observatory",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(auth_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to NTIRO API",
        "docs": "/docs",
        "health": "/health",
        "database_health": "/health/database",
    }
