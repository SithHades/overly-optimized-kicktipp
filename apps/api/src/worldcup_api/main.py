import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from worldcup_api.routers import admin, health, predictions, tournament_tips

app = FastAPI(
    title="WorldCupQuant API",
    version="0.1.0",
    description="Football prediction and Tipp-Spiel optimization API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.environ.get(
            "CORS_ALLOW_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(predictions.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(tournament_tips.router, prefix="/api")
