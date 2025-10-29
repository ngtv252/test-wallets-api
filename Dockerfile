FROM python:3.11-slim AS base

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install --no-install-recommends -y \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Обновляем pip 
RUN pip install --upgrade pip setuptools wheel

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Создаем пользователя для безопасности 
RUN useradd --create-home --shell /bin/bash app

# Production образ
FROM base AS production

# Копируем файлы
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY src/ ./src/

# Устанавливаем права доступа
RUN chown -R app:app /app
USER app

# Открываем порт
EXPOSE 8000

# Команда запуска (--proxy-headers для nginx)
CMD ["python", "-m", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

# Test образ
FROM base AS test

# Копируем файлы
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY src/ ./src/
COPY tests/ ./tests/

# Устанавливаем права доступа
RUN chown -R app:app /app
USER app

# Команда по умолчанию для тестов
CMD ["pytest", "tests/", "-v", "--tb=short"]
