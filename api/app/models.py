"""Modelos ORM que mapean las dos tablas del esquema DBCAMARADETECCIONIM.

Notas del esquema (ver db/sql/camaras.sql):
- La tabla Camara NO declara PRIMARY KEY, pero Id es IDENTITY. A nivel ORM se
  mapea Id como clave primaria (requerido por SQLAlchemy) sin afectar la BD.
- La relación entre tablas es lógica (sin FK): Tr_AforoHistorialHora.IdCamara
  referencia a Camara.IdCamara (el id de negocio), no a Camara.Id.
- IdCamara es bigint en Camara e int en Tr_AforoHistorialHora.
"""
from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Integer,
    Numeric,
    String,
    Unicode,
    UnicodeText,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Camara(Base):
    __tablename__ = "Camara"

    Id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    IdCamara: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    CodigoCamara: Mapped[str | None] = mapped_column(Unicode(200))
    Nombre: Mapped[str | None] = mapped_column(Unicode(200))
    Ciudad: Mapped[str | None] = mapped_column(Unicode(100))
    IpCamara: Mapped[str | None] = mapped_column(Unicode(20))
    IpProcesador: Mapped[str | None] = mapped_column(Unicode(20))
    Activo: Mapped[bool] = mapped_column(Boolean, nullable=False)
    FechaCreacion: Mapped["DateTime"] = mapped_column(DateTime, nullable=False)
    Direccion: Mapped[str | None] = mapped_column(String(500))
    Cy: Mapped[str | None] = mapped_column(String(20))
    Cx: Mapped[str | None] = mapped_column(String(20))
    IdTipoCamara: Mapped[int | None] = mapped_column(Integer)
    IdOrganismotransito: Mapped[str | None] = mapped_column(String(20))
    IdUsuario: Mapped[str | None] = mapped_column(String(20))
    Descripcion: Mapped[str | None] = mapped_column(String(200))
    Enlinea: Mapped[bool | None] = mapped_column(Boolean)


class TrAforoHistorialHora(Base):
    __tablename__ = "Tr_AforoHistorialHora"

    Id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    IdCamara: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    PeriodoInicio: Mapped["DateTime"] = mapped_column(DateTime, nullable=False)
    PeriodoFin: Mapped["DateTime"] = mapped_column(DateTime, nullable=False)
    TotalVehiculos: Mapped[int] = mapped_column(Integer, nullable=False)
    VelocidadPromedio: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    VelocidadMaxima: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    PorCarrilJson: Mapped[str | None] = mapped_column(UnicodeText)
    PorTipoJson: Mapped[str | None] = mapped_column(UnicodeText)
    CambioPorcentajeVehiculos: Mapped[float | None] = mapped_column(Numeric(6, 1))
    CambioPorcentajeVelocidad: Mapped[float | None] = mapped_column(Numeric(6, 1))
    Clasificacion: Mapped[str | None] = mapped_column(String(20))
    FechaRegistro: Mapped["DateTime"] = mapped_column(DateTime, nullable=False)
