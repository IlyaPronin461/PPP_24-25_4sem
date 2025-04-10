# запустить: docker-compose up -d
# остановить: docker-compose down
# пересобрать и запустить: docker-compose up --build -d


from fastapi import FastAPI
from app.api.endpoints import auth, encode
from app.core.config import settings
from app.db.session import create_tables

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(encode.router, prefix="/encode", tags=["encode"])

@app.on_event("startup")
def on_startup():
    create_tables()

@app.get("/", summary="Корневой маршрут", tags=["Основные"])
def read_root():
    return {
        "message": "Welcome to the Encryption Service API",
        "docs": "/docs",
        "redoc": "/redoc"
    }
