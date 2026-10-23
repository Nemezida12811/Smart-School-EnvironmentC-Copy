# IoT Smart School — backend (Python / FastAPI)

Переписаний бекенд із Node/Express. REST- і MQTT-контракт, структура MongoDB та формат відповідей збережені,
тож фронтенд і пристрої працюють без змін.

## Запуск
```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # заповни MONGO_URI, MQTT_URL, JWT_SECRET, GOOGLE_API_KEY
python -m app               # або: uvicorn app.main:app --reload --port 3001
```
Docker: `docker compose up --build`. Тести: `pip install pytest httpx mongomock && pytest`.
Swagger: `/docs`.

## Відповідність Node → Python
| Node | Python |
|---|---|
| express + routes/*.js | FastAPI + `app/routers/*.py` |
| mongodb driver, models/*.js | `pymongo.AsyncMongoClient`, `app/repositories.py` |
| jsonwebtoken / bcrypt | PyJWT / bcrypt (хеші сумісні) |
| mqtt (mqtt.js) | paho-mqtt (`app/mqtt_client.py`), обробка в `app/telemetry.py` |
| @google/genai | google-genai (`app/comfort.py`) |
| verifyTokenMiddleware | залежність `current_user_id` |

## Свідомо збережена поведінка оригіналу (варто переглянути)
- `POST /api/locations/:id/users` не перевіряє, що викликає адмін (у Node ця перевірка закоментована).
- `GET /api/locations/:id` без авторизації.
- Відповідь `.../devices/:id/settings` повертає Wi-Fi пароль і пароль пристрою; їх дефолти (`Admin`/`4444`) тепер у `DEVICE_ADMIN_*`.
- Зберігається лише останнє вимірювання на пристрій (upsert), історії немає.

## Відмінності
- Невалідний ObjectId дає 404, а не 500.
- Бекенд не стартує без `MONGO_URI` / `JWT_SECRET` (у Node лише логувало помилку).
- `PORT` за замовчуванням 3000, як в `index.js`; у Docker задай 3001 в `.env`.
