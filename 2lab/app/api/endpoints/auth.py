from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    get_current_user
)
from app.schemas.user import UserCreate, UserWithToken, User
from app.cruds.user import create_user, get_user_by_email
from app.db.session import get_db

from app.services.huffman import HuffmanCoding
from app.services.xor import XORCipher
from app.schemas.encode import EncodeRequest, EncodeResponse, DecodeRequest, DecodeResponse
from typing import Dict

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


@router.get("/users/me/", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/encode", response_model=EncodeResponse)
async def encode_text(request: EncodeRequest):
    # Сжатие методом хаффмана
    frequency = HuffmanCoding.build_frequency_dict(request.text)
    tree = HuffmanCoding.build_huffman_tree(frequency)
    huffman_codes = HuffmanCoding.build_codes(tree)
    encoded_text, padding = HuffmanCoding.encode_text(request.text, huffman_codes)

    # шифрование с использованием xor
    encrypted_data = XORCipher.encrypt(encoded_text, request.key)

    return EncodeResponse(
        encoded_data=encrypted_data,
        key=request.key,
        huffman_codes=huffman_codes,
        padding=padding
    )


@router.post("/decode", response_model=DecodeResponse)
async def decode_text(request: DecodeRequest):
    # xor расшифровка
    decrypted_data = XORCipher.decrypt(request.encoded_data, request.key)

    # распаковка текста методом хаффмана
    decoded_text = HuffmanCoding.decode_text(
        decrypted_data,
        request.huffman_codes,
        request.padding
    )

    return DecodeResponse(decoded_text=decoded_text)
