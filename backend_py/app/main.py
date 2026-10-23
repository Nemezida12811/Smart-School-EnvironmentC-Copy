import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import database
from .errors import register_handlers
from .mqtt_client import mqtt_client
from .routers import auth, comfort, locations
from .telemetry import handle_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET is not set")
    await database.connect(settings.mongo_uri, settings.mongo_db_name)
    mqtt_client.initialize(asyncio.get_running_loop(), handle_message)
    log.info("✅ Server running on port %s", settings.port)
    yield
    mqtt_client.close()
    await database.disconnect()


app = FastAPI(title="IoT Smart School backend", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
register_handlers(app)

app.include_router(auth.router)
app.include_router(comfort.router)
app.include_router(locations.router)


@app.get("/")
async def root():
    return {"message": "Backend is running"}
