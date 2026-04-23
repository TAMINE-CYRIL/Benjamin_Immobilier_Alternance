from fastapi import FastAPI
from apps.api.routes.auth import router as auth_router
from apps.api.routes.annonces import router as annonces_router

app = FastAPI(title="Benjamin Immobilier API")

app.include_router(auth_router, prefix="/api")
app.include_router(annonces_router, prefix="/api")
