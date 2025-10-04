FROM python:3.11-slim

WORKDIR /app

# Обновление системы и установка основных инструментов
RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Установка зависимостей проекта
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем сервер
COPY server.py .
COPY adapters/ ./adapters/

CMD ["python", "server.py"]
