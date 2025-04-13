# запустить: docker-compose up -d
# остановить: docker-compose down
# пересобрать и запустить: docker-compose up --build -d


# примеры запросов
"""
http://localhost:8000/auth/sign-up/
{
  "email": "user_5@example.com",
  "password": "securepassword123"
}

http://localhost:8000/auth/login/
{
  "email": "user_5@example.com",
  "password": "securepassword123"
}

http://localhost:8000/auth/users/me/
в headers указать:
Key: Authorization
Value: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzVAZXhhbXBsZS5jb20iLCJleHAiOjE3NDQ1NTUzMDh9.Ja647Q11_-dPAMvGEnvYx1d_4B1lcV5tohqrlhQWp68

http://localhost:8000/auth/encode
{
"text": "Hello, World!",
"key": "secret"
}

http://localhost:8000/auth/decode
{
    "encoded_data": "QlVSQ1RFQlVTQ1VFQ1VSQlREQlVTQlRFQ1VTQlRFQlRTQ1RFQ1RSQlVFQ1VTQlVE",
    "key": "secret",
    "huffman_codes": {
        "o": "00",
        "l": "01",
        " ": "1000",
        "!": "1001",
        ",": "1010",
        "H": "1011",
        "W": "1100",
        "d": "1101",
        "e": "1110",
        "r": "1111"
    },
    "padding": 6
}
"""


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
