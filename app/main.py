from fastapi import FastAPI

from app.database import init_db
from app.routers import auth, users, events

app = FastAPI(title="Mental Health App API")


@app.on_event("startup")
def on_startup():
    # Enables uuid-ossp and creates tables if they don't already exist.
    # Fine for local dev; swap for Alembic migrations later.
    init_db()


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(events.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
