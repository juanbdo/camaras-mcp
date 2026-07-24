"""Endpoints del maestro de cámaras."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Camara, TrAforoHistorialHora
from app.schemas import AforoOut, CamaraOut
from app.security import get_current_user

router = APIRouter(
    prefix="/camaras",
    tags=["camaras"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "",
    response_model=list[CamaraOut],
    operation_id="listar_camaras",
    summary="Listar cámaras",
    description="Lista las cámaras con filtros opcionales por ciudad, estado y tipo.",
)
def listar_camaras(
    db: Session = Depends(get_db),
    ciudad: str | None = Query(None, description="Filtrar por ciudad (coincidencia parcial)"),
    activo: bool | None = Query(None, description="Filtrar por estado activo/inactivo"),
    id_tipo_camara: int | None = Query(None, description="Filtrar por IdTipoCamara"),
    skip: int = Query(0, ge=0, description="Registros a omitir (paginación)"),
    limit: int = Query(50, ge=1, le=500, description="Máximo de registros a devolver"),
) -> list[Camara]:
    stmt = select(Camara)
    if ciudad:
        stmt = stmt.where(Camara.Ciudad.like(f"%{ciudad}%"))
    if activo is not None:
        stmt = stmt.where(Camara.Activo == activo)
    if id_tipo_camara is not None:
        stmt = stmt.where(Camara.IdTipoCamara == id_tipo_camara)
    stmt = stmt.order_by(Camara.IdCamara).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


@router.get(
    "/{id_camara}",
    response_model=CamaraOut,
    operation_id="obtener_camara",
    summary="Obtener una cámara",
    description="Devuelve el detalle de una cámara por su IdCamara (id de negocio).",
)
def obtener_camara(
    id_camara: int,
    db: Session = Depends(get_db),
) -> Camara:
    camara = db.scalar(select(Camara).where(Camara.IdCamara == id_camara))
    if camara is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe la cámara con IdCamara={id_camara}",
        )
    return camara


@router.get(
    "/{id_camara}/aforo",
    response_model=list[AforoOut],
    operation_id="listar_aforo_de_camara",
    summary="Aforo de una cámara",
    description=(
        "Lista los registros de aforo por hora de una cámara, con rango de "
        "fechas opcional sobre PeriodoInicio."
    ),
)
def listar_aforo_de_camara(
    id_camara: int,
    db: Session = Depends(get_db),
    desde: datetime | None = Query(None, description="PeriodoInicio >= desde (ISO 8601)"),
    hasta: datetime | None = Query(None, description="PeriodoInicio <= hasta (ISO 8601)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[AforoOut]:
    # Verifica que la cámara exista para dar un 404 claro.
    if db.scalar(select(Camara.Id).where(Camara.IdCamara == id_camara)) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe la cámara con IdCamara={id_camara}",
        )
    stmt = select(TrAforoHistorialHora).where(
        TrAforoHistorialHora.IdCamara == id_camara
    )
    if desde is not None:
        stmt = stmt.where(TrAforoHistorialHora.PeriodoInicio >= desde)
    if hasta is not None:
        stmt = stmt.where(TrAforoHistorialHora.PeriodoInicio <= hasta)
    stmt = stmt.order_by(TrAforoHistorialHora.PeriodoInicio).offset(skip).limit(limit)
    return [AforoOut.from_orm_row(r) for r in db.scalars(stmt).all()]
