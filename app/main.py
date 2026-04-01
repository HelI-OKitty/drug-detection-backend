from fastapi import FastAPI
from app.api.health_api import router as health_router

app = FastAPI()

app.include_router(health_router)

@app.get("/")
def root():
    return {"msg": "backend running"}