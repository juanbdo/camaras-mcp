#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Inicializa la base de datos del demo:
#   1. Espera a que SQL Server acepte conexiones.
#   2. Crea la base de datos si no existe (el script camaras.sql NO la crea,
#      solo hace USE [DBCAMARADETECCIONIM]).
#   3. Ejecuta camaras.sql (DDL + datos semilla) con sqlcmd, que entiende los
#      separadores GO y las sentencias SET IDENTITY_INSERT.
# Es idempotente: si la BD ya tiene la tabla Camara, no vuelve a cargar.
# ---------------------------------------------------------------------------
set -euo pipefail

DB_NAME="${MSSQL_DB:-DBCAMARADETECCIONIM}"
SA_PASSWORD="${MSSQL_SA_PASSWORD:?MSSQL_SA_PASSWORD no definido}"
SQL_FILE="/sql/camaras.sql"

# Localiza sqlcmd (la ruta cambió entre imágenes de mssql-tools 17 y 18).
if command -v sqlcmd >/dev/null 2>&1; then
  SQLCMD="sqlcmd"
elif [ -x /opt/mssql-tools18/bin/sqlcmd ]; then
  SQLCMD="/opt/mssql-tools18/bin/sqlcmd"
elif [ -x /opt/mssql-tools/bin/sqlcmd ]; then
  SQLCMD="/opt/mssql-tools/bin/sqlcmd"
else
  echo "ERROR: no se encontró sqlcmd en la imagen." >&2
  exit 1
fi

# -C = confiar en el certificado (self-signed de SQL Server); -b = abortar en error.
run_sql() { "$SQLCMD" -S "sqlserver,1433" -U sa -P "$SA_PASSWORD" -C -b "$@"; }

echo ">> Esperando a que SQL Server acepte conexiones..."
for i in $(seq 1 60); do
  if run_sql -Q "SELECT 1" >/dev/null 2>&1; then
    echo ">> SQL Server disponible."
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "ERROR: SQL Server no respondió tras 60 intentos." >&2
    exit 1
  fi
  sleep 2
done

echo ">> Creando la base de datos [$DB_NAME] si no existe..."
run_sql -Q "IF DB_ID(N'$DB_NAME') IS NULL CREATE DATABASE [$DB_NAME];"

# Comprueba si los datos ya fueron cargados (idempotencia).
ALREADY=$(run_sql -d "$DB_NAME" -h -1 -W \
  -Q "SET NOCOUNT ON; IF OBJECT_ID(N'dbo.Camara') IS NOT NULL SELECT 1 ELSE SELECT 0" \
  | tr -d '[:space:]')

if [ "$ALREADY" = "1" ]; then
  echo ">> La tabla dbo.Camara ya existe. Se omite la carga (idempotente)."
else
  echo ">> Cargando esquema y datos desde $SQL_FILE ..."
  run_sql -d "$DB_NAME" -i "$SQL_FILE"
  echo ">> Carga completada."
fi

echo ">> Verificación:"
run_sql -d "$DB_NAME" -Q "SELECT 'Camara' AS Tabla, COUNT(*) AS Filas FROM dbo.Camara UNION ALL SELECT 'Tr_AforoHistorialHora', COUNT(*) FROM dbo.Tr_AforoHistorialHora;"

echo ">> Inicialización finalizada correctamente."
