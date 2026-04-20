from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.auth import router as auth_router
from app.db.redis_client import redis_client
from app.db.base import Base
from app.db.session import engine
from app.models.user_table import User

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await redis_client.ping()
        print("Redis connected")
    except Exception as e:
        print("Redis not available:", e)
    yield
    try:
        await redis_client.aclose()
    except Exception:
        pass


app = FastAPI(title="fastapi-demo", lifespan=lifespan)

app.include_router(auth_router)


@app.get("/")
async def root():
    return {"message": "service is running"}