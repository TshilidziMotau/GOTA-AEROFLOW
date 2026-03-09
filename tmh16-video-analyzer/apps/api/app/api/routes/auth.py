from fastapi import APIRouter, HTTPException
from app.schemas.schemas import LoginRequest, LoginResponse
from app.services.auth import create_token

router = APIRouter()


@router.post('/login', response_model=LoginResponse)
def login(payload: LoginRequest):
    if not payload.email or not payload.password:
        raise HTTPException(status_code=400, detail='Invalid credentials')
    return LoginResponse(access_token=create_token(payload.email))
