"""Endpoints de aforo (mediciones por hora) y agregaciones."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Camara, TrAforoHistorialHora
from app.schemas import AforoOut, ResumenAforo, ResumenItem
from app.security import get_current_user

router = APIRouter(
    prefix="/aforo",
    tags=["aforo"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "",
    response_model=list[AforoOut],
    operation_id="listar_aforo",
    summary="Listar registros de aforo",
    description=(
        "Lista mediciones de aforo por hora con filtros por cámara, rango de "
        "fechas y clasificación. Los campos JSON (por carril y por tipo) se "
        "devuelven ya parseados."
    ),
)
def listar_aforo(
    db: Session = Depends(get_db),
    id_camara: int | None = Query(None, description="Filtrar por IdCamara"),
    desde: datetime | None = Query(None, description="PeriodoInicio >= desde (ISO 8601)"),
    hasta: datetime | None = Query(None, description="PeriodoInicio <= hasta (ISO 8601)"),
    clasificacion: str | None = Query(
        None, description="Filtrar por Clasificacion (Estable, Aumento, Reduccion)"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[AforoOut]:
    stmt = select(TrAforoHistorialHora)
    if id_camara is not None:
        stmt = stmt.where(TrAforoHistorialHora.IdCamara == id_camara)
    if desde is not None:
        stmt = stmt.where(TrAforoHistorialHora.PeriodoInicio >= desde)
    if hasta is not None:
        stmt = stmt.where(TrAforoHistorialHora.PeriodoInicio <= hasta)
    if clasificacion:
        stmt = stmt.where(TrAforoHistorialHora.Clasificacion == clasificacion)
    stmt = stmt.order_by(TrAforoHistorialHora.PeriodoInicio).offset(skip).limit(limit)
    return [AforoOut.from_orm_row(r) for r in db.scalars(stmt).all()]


@router.get(
    "/resumen",
    response_model=ResumenAforo,
    operation_id="resumen_aforo",
    summary="Resumen agregado de aforo",
    description=(
        "Calcula agregados de aforo (total de vehículos, velocidad promedio y "
        "máxima, y conteo por clasificación). Con group_by=camara desglosa por "
        "cámara; con group_by=global entrega un único total."
    ),
)
def resumen_aforo(
    db: Session = Depends(get_db),
    id_camara: int | None = Query(None, description="Limitar el resumen a una cámara"),
    desde: datetime | None = Query(None, description="PeriodoInicio >= desde (ISO 8601)"),
    hasta: datetime | None = Query(None, description="PeriodoInicio <= hasta (ISO 8601)"),
    group_by: str = Query(
        "camara", pattern="^(camara|global)$", description="camara | global"
    ),
) -> ResumenAforo:
    T = TrAforoHistorialHora

    def apply_filters(stmt):
        if id_camara is not None:
            stmt = stmt.where(T.IdCamara == id_camara)
        if desde is not None:
            stmt = stmt.where(T.PeriodoInicio >= desde)
        if hasta is not None:
            stmt = stmt.where(T.PeriodoInicio <= hasta)
        return stmt

    grouped = group_by == "camara"
    group_cols = [T.IdCamara] if grouped else []

    agg_stmt = apply_filters(
        select(
            *group_cols,
            func.count().label("registros"),
            func.coalesce(func.sum(T.TotalVehiculos), 0).label("total"),
            func.coalesce(func.avg(T.VelocidadPromedio), 0).label("vel_prom"),
            func.coalesce(func.max(T.VelocidadMaxima), 0).label("vel_max"),
        )
    )
    if grouped:
        agg_stmt = agg_stmt.group_by(T.IdCamara).order_by(T.IdCamara)

    # Conteo por clasificación (query aparte, agrupada).
    clas_cols = [T.IdCamara] if grouped else []
    clas_stmt = apply_filters(
        select(*clas_cols, T.Clasificacion, func.count().label("n"))
    ).group_by(*clas_cols, T.Clasificacion)

    clas_map: dict[int | None, dict[str, int]] = {}
    for row in db.execute(clas_stmt):
        key = row.IdCamara if grouped else None
        label = row.Clasificacion or "SinClasificar"
        clas_map.setdefault(key, {})[label] = row.n

    # Nombres de cámara para enriquecer la salida.
    nombres: dict[int, str | None] = {}
    if grouped:
        for cid, nombre in db.execute(select(Camara.IdCamara, Camara.Nombre)):
            nombres[cid] = nombre

    items: list[ResumenItem] = []
    for row in db.execute(agg_stmt):
        cid = row.IdCamara if grouped else None
        items.append(
            ResumenItem(
                IdCamara=cid,
                NombreCamara=nombres.get(cid) if cid is not None else None,
                Registros=row.registros,
                TotalVehiculos=int(row.total),
                VelocidadPromedio=round(float(row.vel_prom), 2),
                VelocidadMaxima=round(float(row.vel_max), 2),
                PorClasificacion=clas_map.get(cid, {}),
            )
        )

    return ResumenAforo(group_by=group_by, items=items)


@router.get(
    "/{id}",
    response_model=AforoOut,
    operation_id="obtener_aforo",
    summary="Obtener un registro de aforo",
    description="Devuelve un registro de aforo por su Id, con los campos JSON parseados.",
)
def obtener_aforo(
    id: int,
    db: Session = Depends(get_db),
) -> AforoOut:
    row = db.scalar(
        select(TrAforoHistorialHora).where(TrAforoHistorialHora.Id == id)
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe el registro de aforo con Id={id}",
        )
    return AforoOut.from_orm_row(row)
