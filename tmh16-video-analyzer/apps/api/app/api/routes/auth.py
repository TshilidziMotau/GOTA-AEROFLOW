from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.schemas import LoginRequest, LoginResponse, MeResponse
from app.services.auth import authenticate_user, create_token, CurrentUser, get_current_user

router = APIRouter()


@router.post('/login', response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail='Invalid credentials')
    return LoginResponse(access_token=create_token(user.email, user.role), role=user.role)


@router.get('/me', response_model=MeResponse)
def me(user: CurrentUser = Depends(get_current_user)):
    return MeResponse(email=user.email, role=user.role)
