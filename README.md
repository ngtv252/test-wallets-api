# Структура проекта

```
src/
├── api/v1/          # API эндпоинты
├── core/            # Основная логика
├── wallet/          # Cлой логики кошельков
└── app.py           # Точка входа

tests/               # Тесты
alembic/             # Миграции БД
docker-compose.yml   # Конфигурация Docker
docker-compose.test.yml   # Конфигурация Docker для тестов
```


### Установка Docker и Docker Compose

**Для Ubuntu/Debian:**
```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Проверка установки
docker --version
docker-compose --version
```

**Для Windows:**
- Скачайте и установите [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Docker Compose входит в состав Docker Desktop

**Для macOS:**
```bash
# Через Homebrew
brew install --cask docker

# Или скачайте Docker Desktop для Mac
# https://www.docker.com/products/docker-desktop/
```

**Альтернативные инструкции:**
- [Официальная документация Docker](https://docs.docker.com/engine/install/ubuntu/)
- [Официальная документация Docker Compose](https://docs.docker.com/compose/install/)

---
## Подготовка

### 1. Копируем файлы проекта

```bash
git clone <repository-url>
```

### 2. Настройка переменных окружения

Создайте файл `.env` и отредактируйте необходимые параметры

```bash
cp env.example .env
```

### 3. Тесты

1. Быстрые локальные тесты (SQLite, без конкурентности):
   ```bash
   pytest -v
   ```

2. Полные тесты в Docker (PostgreSQL, включая конкурентность):
   ```bash
   docker compose -f docker-compose.test.yml up --build --exit-code-from tests
   ```


### 4. Сборка Docker образов

```bash
docker-compose build
```

# Запуск 

```bash
docker-compose up -d
```

Сервисы запустятся в фоновом режиме:
- **PostgreSQL** - БД
- **Migrator** - one-shot сервис миграций
- **Backend** - FastAPI backend
- **Nginx** - reverse proxy

### Проверка статуса сервисов

```bash
docker-compose ps
```

### API Healthcheck
```bash
curl localhost/ping
```

```json
{"status": "OK", "message": "Pong"}
```