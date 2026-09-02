from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.analysis_api import router as analysis_router
from app.api.config_api import router as config_router
from app.api.detection_api import router as detection_router
from app.api.auth_api import router as auth_router
from app.api.health_api import router as health_router
from app.db.mongo import create_indexes


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_indexes()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(health_router)
app.include_router(detection_router)
app.include_router(analysis_router)
app.include_router(config_router)
app.include_router(auth_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.get("/")
def root():
    return {"msg": "backend running"}
