from jose import jwt
from app.core.config import settings


def create_token(subject: str) -> str:
    return jwt.encode({'sub': subject}, settings.jwt_secret, algorithm='HS256')
