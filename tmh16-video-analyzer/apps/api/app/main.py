from fastapi import FastAPI
from app.api.router import api_router
from app.db.session import Base, engine
from app.models import models  # noqa: F401

app = FastAPI(title="TMH16 Video Analyzer API", version="0.1.0")
app.include_router(api_router)


@app.on_event('startup')
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get('/health')
def health() -> dict[str, str]:
    return {"status": "ok"}
