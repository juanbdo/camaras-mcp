"""Endpoint de autenticación (OAuth2 password flow -> JWT)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas import Token
from app.security import authenticate_user, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/token",
    response_model=Token,
    operation_id="login",
    summary="Obtener un token JWT",
    description=(
        "Autentica un usuario semilla (por defecto admin/admin123 o demo/demo123) "
        "y devuelve un token Bearer JWT para usar en el resto de endpoints."
    ),
)
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    username = authenticate_user(form_data.username, form_data.password)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(username))
