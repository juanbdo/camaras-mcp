"""Autenticación con OAuth2 password flow + JWT sobre usuarios semilla.

Los usuarios viven en la variable de entorno DEMO_USERS (ver config). No hay
tabla de usuarios: es intencional para mantener el demo simple. El mismo
`get_current_user` protege los endpoints del API y, vía passthrough, las tools
del servidor MCP.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()

# tokenUrl relativo -> el botón "Authorize" de Swagger usa POST /auth/token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciales inválidas o token ausente",
    headers={"WWW-Authenticate": "Bearer"},
)


def authenticate_user(username: str, password: str) -> str | None:
    """Verifica usuario/contraseña contra los usuarios semilla."""
    expected = settings.users_map.get(username)
    if expected is None:
        return None
    if not secrets.compare_digest(password, expected):
        return None
    return username


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Valida el JWT y devuelve el nombre de usuario (subject)."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        username = payload.get("sub")
        if not username:
            raise _CREDENTIALS_EXC
    except JWTError as exc:
        raise _CREDENTIALS_EXC from exc
    return username
