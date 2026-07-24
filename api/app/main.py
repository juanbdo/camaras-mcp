"""Punto de entrada del API + servidor MCP.

El servidor MCP se construye con FastAPI-MCP a partir de la especificación
OpenAPI del propio API: cada operación se expone como una tool MCP. La
autenticación es passthrough JWT: el cliente MCP envía el header
Authorization: Bearer <token> y FastAPI-MCP lo reenvía a los endpoints, que lo
validan con el mismo get_current_user usado por Swagger.
"""
from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi_mcp import AuthConfig, FastApiMCP

from app.routers import aforo, auth, camaras
from app.security import get_current_user

app = FastAPI(
    title="Cámaras & Aforo API",
    version="1.0.0",
    description=(
        "API de demostración sobre las tablas Camara y Tr_AforoHistorialHora. "
        "Autenticación JWT (OAuth2 password flow). Expuesta como servidor MCP "
        "en la ruta /mcp mediante FastAPI-MCP."
    ),
)

app.include_router(auth.router)
app.include_router(camaras.router)
app.include_router(aforo.router)


@app.get("/health", tags=["infra"], operation_id="health", summary="Healthcheck")
def health() -> dict[str, str]:
    """Endpoint público de salud (sin autenticación)."""
    return {"status": "ok"}


# --- Servidor MCP -----------------------------------------------------------
# Se construye después de registrar todas las rutas para capturar el OpenAPI
# completo. AuthConfig exige el Bearer token para conectarse al MCP y lo
# reenvía a los endpoints (passthrough JWT).
mcp = FastApiMCP(
    app,
    name="Camaras Aforo MCP",
    auth_config=AuthConfig(dependencies=[Depends(get_current_user)]),
)
mcp.mount_http()
