from fastapi import FastAPI
from apps.api.routes.annonces import router as annonces_router

app = FastAPI(title="Benjamin Immobilier API")

app.include_router(annonces_router, prefix="/api")