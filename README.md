# Demo MCP — Cámaras & Aforo

Demostración end-to-end de cómo un **servidor MCP** permite a un cliente (por
ejemplo Claude) acceder e interactuar con los datos de una base de datos.

La demo levanta, en un único grupo de contenedores llamado **`mcp-demo`**:

| Servicio     | Contenedor              | Descripción                                             | Puerto |
|--------------|-------------------------|---------------------------------------------------------|--------|
| `sqlserver`  | `mcp-demo-sqlserver`    | SQL Server 2022 **Developer** (gratis, sin licencia)    | 1433   |
| `db-init`    | `mcp-demo-db-init`      | Crea la BD y carga `db/sql/camaras.sql` (one-shot)      | —      |
| `adminer`    | `mcp-demo-adminer`      | Herramienta web para consultar la BD                    | 8080   |
| `api`        | `mcp-demo-api`          | API **FastAPI** con JWT + servidor **MCP** (FastAPI-MCP)| 8000   |

Datos: dos tablas —`Camara` (maestro de cámaras) y `Tr_AforoHistorialHora`
(mediciones de aforo por hora, con desgloses JSON por carril y por tipo de
vehículo)—.

---

## Requisitos

- Docker Desktop (o Docker Engine + Compose v2).

## 1. Levantar el demo

```bash
# (opcional) revisar/ajustar credenciales; ya viene un .env con valores demo
cp .env.example .env      # solo si no existe .env

docker compose up -d --build
```

- Todos los contenedores quedan agrupados bajo el proyecto **`mcp-demo`**
  (visible en Docker Desktop o con `docker compose ls`).
- `db-init` crea la base `DBCAMARADETECCIONIM` (el script SQL solo hace `USE`,
  no `CREATE DATABASE`) y carga esquema + datos con `sqlcmd`. Es idempotente.
- SQL Server tarda ~20–40 s en quedar listo; `api` y `adminer` esperan a que
  esté sano y a que `db-init` termine.

Ver el estado / logs de la carga inicial:

```bash
docker compose ps
docker compose logs db-init
docker compose logs api
```

## 2. Consultar la BD con Adminer

Abrir <http://localhost:8080> y conectar con:

| Campo    | Valor                  |
|----------|------------------------|
| Motor    | **MS SQL**             |
| Servidor | `sqlserver`            |
| Usuario  | `sa`                   |
| Password | `Dev_Camaras_2026!`    |
| Base     | `DBCAMARADETECCIONIM`  |

Deberían verse las tablas `Camara` (4 filas) y `Tr_AforoHistorialHora`.

## 3. Probar el API vía Swagger

Abrir <http://localhost:8000/docs>.

1. Click en **Authorize**.
2. Usuario `admin`, contraseña `admin123` (o `demo` / `demo123`). Dejar
   client id/secret en blanco. Click **Authorize**.
3. Probar los endpoints:
   - `GET /camaras` — listado con filtros (`ciudad`, `activo`, `id_tipo_camara`).
   - `GET /camaras/{id_camara}` — detalle (ej. `22` o `9`).
   - `GET /camaras/{id_camara}/aforo` — aforo de una cámara.
   - `GET /aforo` — mediciones con filtros; los campos JSON llegan parseados.
   - `GET /aforo/{id}` — una medición por Id.
   - `GET /aforo/resumen?group_by=camara` — **agregaciones** (total vehículos,
     velocidad promedio/máxima, conteo por clasificación).

Sin token, los endpoints de datos responden **401**.

> Obtener un token por consola (útil para MCP):
> ```bash
> curl -s -X POST http://localhost:8000/auth/token \
>   -d "username=admin&password=admin123" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])"
> ```

## 4. Usar el servidor MCP

El servidor MCP se genera automáticamente desde el OpenAPI del API con
**FastAPI-MCP** (`mount_http()`), y queda expuesto en:

```
http://localhost:8000/mcp
```

Cada operación del API es una **tool** MCP (`listar_camaras`, `obtener_camara`,
`listar_aforo`, `resumen_aforo`, etc.). La autenticación es **passthrough JWT**:
el cliente MCP debe enviar el header `Authorization: Bearer <token>`, que se
valida contra el mismo mecanismo del API.

### Configuración en un cliente MCP (ej. Claude Desktop / Claude Code)

Usando un proxy stdio→HTTP como `mcp-remote`:

```json
{
  "mcpServers": {
    "camaras-aforo": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://localhost:8000/mcp",
        "--header",
        "Authorization: Bearer PEGA_AQUI_TU_TOKEN"
      ]
    }
  }
}
```

Reemplazar `PEGA_AQUI_TU_TOKEN` por el token obtenido en el paso 3. Luego, desde
el cliente MCP, se pueden listar las tools y ejecutarlas (por ejemplo
`resumen_aforo` con `group_by=camara`), obteniendo los mismos datos que el API.

## Detener / limpiar

```bash
docker compose down       # detiene y elimina contenedores
docker compose down -v    # además borra el volumen de datos de SQL Server
```

---

## Estructura del proyecto

```
camaras-mcp/
├── docker-compose.yml        # grupo mcp-demo: sqlserver, db-init, adminer, api
├── .env / .env.example       # credenciales y configuración
├── db/
│   ├── sql/camaras.sql        # esquema + datos semilla (SQL Server)
│   └── init/init.sh           # crea la BD y carga el script con sqlcmd
└── api/
    ├── Dockerfile
    ├── requirements.txt
    └── app/
        ├── main.py            # app FastAPI + montaje del servidor MCP
        ├── config.py          # settings (env)
        ├── database.py        # engine SQLAlchemy (mssql+pymssql)
        ├── models.py          # ORM: Camara, TrAforoHistorialHora
        ├── schemas.py         # Pydantic (incl. parseo de campos JSON)
        ├── security.py        # OAuth2 + JWT (usuarios semilla)
        └── routers/           # auth, camaras, aforo
```

## Notas técnicas

- **Sin licencias**: `MSSQL_PID=Developer` (edición gratuita para desarrollo).
- **Driver**: `pymssql` (wheel con FreeTDS embebido) — no requiere ODBC.
- **Relación lógica**: `Tr_AforoHistorialHora.IdCamara` referencia a
  `Camara.IdCamara` (id de negocio); no hay FK física en el esquema.
- Si Adminer tuviera problemas con el driver MS SQL, la alternativa es sustituir
  el servicio `adminer` por **CloudBeaver** (`dbeaver/cloudbeaver`).
