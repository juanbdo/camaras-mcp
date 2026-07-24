"""Esquemas Pydantic (contratos de entrada/salida del API)."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------------------------------
# Autenticación
# --------------------------------------------------------------------------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --------------------------------------------------------------------------
# Cámaras
# --------------------------------------------------------------------------
class CamaraOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: int
    IdCamara: int
    CodigoCamara: str | None = None
    Nombre: str | None = None
    Ciudad: str | None = None
    IpCamara: str | None = None
    IpProcesador: str | None = None
    Activo: bool
    FechaCreacion: datetime
    Direccion: str | None = None
    Cy: str | None = None
    Cx: str | None = None
    IdTipoCamara: int | None = None
    IdOrganismotransito: str | None = None
    Descripcion: str | None = None
    Enlinea: bool | None = None


# --------------------------------------------------------------------------
# Aforo
# --------------------------------------------------------------------------
class CarrilItem(BaseModel):
    CarrilId: int
    TotalVehiculos: int
    Porcentaje: float
    VelocidadPromedio: float
    VelocidadMaxima: float | None = None


class TipoItem(BaseModel):
    Tipo: str
    Cantidad: int
    Porcentaje: float
    VelocidadPromedio: float
    VelocidadMaxima: float | None = None


def _parse_json_list(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except (ValueError, TypeError):
        return []


class AforoOut(BaseModel):
    """Registro de aforo con los campos JSON ya parseados a listas tipadas."""

    model_config = ConfigDict(from_attributes=True)

    Id: int
    IdCamara: int
    PeriodoInicio: datetime
    PeriodoFin: datetime
    TotalVehiculos: int
    VelocidadPromedio: float
    VelocidadMaxima: float
    CambioPorcentajeVehiculos: float | None = None
    CambioPorcentajeVelocidad: float | None = None
    Clasificacion: str | None = None
    FechaRegistro: datetime
    PorCarril: list[CarrilItem] = Field(default_factory=list)
    PorTipo: list[TipoItem] = Field(default_factory=list)

    @classmethod
    def from_orm_row(cls, row: Any) -> "AforoOut":
        """Construye la respuesta parseando PorCarrilJson / PorTipoJson."""
        return cls(
            Id=row.Id,
            IdCamara=row.IdCamara,
            PeriodoInicio=row.PeriodoInicio,
            PeriodoFin=row.PeriodoFin,
            TotalVehiculos=row.TotalVehiculos,
            VelocidadPromedio=float(row.VelocidadPromedio),
            VelocidadMaxima=float(row.VelocidadMaxima),
            CambioPorcentajeVehiculos=(
                float(row.CambioPorcentajeVehiculos)
                if row.CambioPorcentajeVehiculos is not None
                else None
            ),
            CambioPorcentajeVelocidad=(
                float(row.CambioPorcentajeVelocidad)
                if row.CambioPorcentajeVelocidad is not None
                else None
            ),
            Clasificacion=row.Clasificacion,
            FechaRegistro=row.FechaRegistro,
            PorCarril=[CarrilItem(**c) for c in _parse_json_list(row.PorCarrilJson)],
            PorTipo=[TipoItem(**t) for t in _parse_json_list(row.PorTipoJson)],
        )


# --------------------------------------------------------------------------
# Resumen / agregaciones
# --------------------------------------------------------------------------
class ResumenItem(BaseModel):
    IdCamara: int | None = None
    NombreCamara: str | None = None
    Registros: int
    TotalVehiculos: int
    VelocidadPromedio: float
    VelocidadMaxima: float
    PorClasificacion: dict[str, int] = Field(default_factory=dict)


class ResumenAforo(BaseModel):
    group_by: str
    items: list[ResumenItem]
