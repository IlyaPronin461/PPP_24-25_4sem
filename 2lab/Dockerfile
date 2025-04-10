FROM python:3.9-slim

WORKDIR /code

# системные зависимости для сборки пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# pip зеркало для ускорения загрузки
RUN pip install --upgrade pip --timeout 1000 && \
    pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

COPY requirements.txt .

# увеличиваем таймаут
RUN pip install --no-cache-dir --timeout 1000 -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]