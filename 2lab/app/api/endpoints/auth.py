from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.core.security import (
    create_access_token,
    verify_password,
    get_password_hash
)
from app.schemas.user import UserCreate, UserWithToken
from app.cruds.user import create_user, get_user_by_email
from app.db.session import get_db

router = APIRouter()


@router.post("/sign-up/", response_model=UserWithToken)
def sign_up(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    user_in = UserCreate(email=user.email, password=hashed_password)
    created_user = create_user(db=db, user=user_in)

    # генерация токена
    access_token_expires = timedelta(minutes=30)  # сколько будет существовать наш токен
    access_token = create_access_token(
        data={"sub": created_user.email}, expires_delta=access_token_expires
    )

    return {
        "id": created_user.id,
        "email": created_user.email,
        "token": access_token
    }


@router.post("/login/", response_model=UserWithToken)
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user.email)

    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # генерация нового токена
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )

    return {
        "id": db_user.id,
        "email": db_user.email,
        "token": access_token
    }