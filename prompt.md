Quiero hacer una demostración del uso de MCP para acceder e interactuar con la información de un par de tablas de una base de datos. Para ello se deben tener en cuenta las siguientes consideraciones:

- El script “db/sql/camara.sql” contiene las instrucciones para crear y poblar una base de datos de SQLServer con dos tablas: la de “Camara” con el maestro de la información básica de una cámara y “Tr_AforoHistorialHora” con el aforo o mediciones que calcula el servicio. 

- Quiero un contenedor de Docker con una instancia de la base de datos en una versión de SQLServer en la que no se tengan problemas de licencias para correr el demo; también quiero que en otro contenedor se monte una herramienta de acceso a la base de datos para consultar los datos.

- Quiero que todos los contenedores de Docker que se van a crear en esta demostración queden dentro de un grupo de contenedores llamado mcp-demo.

- Quiero que crees un API usando FastAPI con los servicios básicos que se puedan derivar de estas dos tablas y la estrategia que consideres pertinente para resolver los asuntos de infraestructura; por ejemplo, la autenticación con JWT la puedes hacer por la vía que consideres, puede ser usando FastAPIUser o cualquier otra estrategia, lo que se necesita es que al momento de probar el API vía el Swagger en Openapi que provee FastAPI, no se tenga ningún inconveniente, al igual que el servidor MCP no tenga problema para el acceso a los servicios del API.

- Para la construcción del servidor MCP quiero que utilices FastAPI-MCP para generar el servidor MCP a partir de su especificación OpenAPI.