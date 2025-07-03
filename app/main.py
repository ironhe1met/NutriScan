from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="NutriScan API")

app.include_router(router)
