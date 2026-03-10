from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.db.session import Base, SessionLocal, engine
from app.models import models  # noqa: F401
from app.models.models import User
from app.services.auth import hash_password

app = FastAPI(title='TMH16 Video Analyzer API', version='0.1.0')
app.include_router(api_router)


@app.on_event('startup')
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == settings.admin_email).first()
        if not admin:
            db.add(User(email=settings.admin_email, password_hash=hash_password(settings.admin_password), role='admin'))
            db.commit()
    finally:
        db.close()


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}
