
from fastapi import FastAPI

app = FastAPI(
    title="NTIRO API",
    description="National Threat & Risk Intelligence Observatory",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "Welcome to NTIRO API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "project": "NTIRO",
    }
