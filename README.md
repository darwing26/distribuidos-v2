# Sistema Distribuido de Procesamiento de Imágenes

## Descripción

Sistema distribuido para procesamiento de imágenes en paralelo que permite a los usuarios enviar lotes de imágenes para aplicar diversas transformaciones utilizando múltiples nodos de procesamiento.

## Arquitectura del Sistema

```
┌─────────────┐    HTTPS    ┌──────────────────┐    SOAP     ┌─────────────────┐
│  App Web    │◄────────────►│ Backend Capa     │◄────────────►│ Servidor de     │
│  Cliente    │             │ Cliente          │             │ Aplicación      │
└─────────────┘             └──────────────────┘             │ Python          │
                                                             └─────────────────┘
                                                                     │
                                                                   SOAP
                                                                     ▼
                            ┌─────────────────┐    Socket TCP   ┌─────────────────┐
                            │ Servidor de     │◄────────────────►│ Base de Datos   │
                            │ Aplicación      │                 │ MySQL           │
                            │ Python          │                 └─────────────────┘
                            └─────────────────┘
                                    │
                                  gRPC
                            ┌───────┼───────┐
                            ▼       ▼       ▼
                    ┌──────────┐ ┌──────────┐ ┌──────────┐
                    │  Nodo 1  │ │  Nodo 2  │ │  Nodo N  │
                    │   JAVA   │ │   JAVA   │ │   JAVA   │
                    └──────────┘ └──────────┘ └──────────┘
```

## Características

### Transformaciones Soportadas
1. **Conversión a escala de grises**
2. **Redimensionar** - Cambiar tamaño manteniendo o no la proporción
3. **Recortar** - Extraer una región específica
4. **Rotar** - Rotar por ángulos específicos
5. **Reflejar** - Espejo horizontal/vertical
6. **Desenfocar** - Aplicar filtro de desenfoque
7. **Perfilar (nitidez)** - Mejorar la nitidez
8. **Ajuste de brillo y contraste**
9. **Inserción de marcas de agua o texto**
10. **Conversión de formato** - JPG, PNG, TIF, BMP

### Protocolos de Comunicación
- **SOAP**: Comunicación entre backend cliente y servidor de aplicación
- **gRPC**: Comunicación entre servidor de aplicación y nodos
- **Socket TCP**: Comunicación con base de datos MySQL
- **REST API**: Interfaz Swagger para pruebas y desarrollo

## Instalación y Configuración

### Prerrequisitos
- Python 3.8+
- MySQL Server
- Windows (PowerShell)

### Instalación
```bash
# 1. Clonar o descargar el proyecto
# 2. Ejecutar script de inicialización
init.bat

# 3. Configurar base de datos MySQL
# Ejecutar el script SQL en database/create_tables.sql

# 4. Configurar variables de entorno (opcional)
# Editar archivo .env con tus configuraciones
```

### Base de Datos
```sql
-- Crear base de datos
CREATE DATABASE sistema_imagenes;

-- Ejecutar script completo
source database/create_tables.sql;
```

## Uso del Sistema

### 1. Iniciar Servidor de Aplicación
```bash
cd servidor_aplicacion
python main.py
```
El servidor estará disponible en: http://localhost:8000

### 2. Iniciar Nodos de Procesamiento
```bash
# Nodo 1
python nodos\nodo.py --node-id nodo-001 --port 50051

# Nodo 2
python nodos\nodo.py --node-id nodo-002 --port 50052

# Nodo 3
python nodos\nodo.py --node-id nodo-003 --port 50053
```

### 3. Acceder a las Interfaces

#### Swagger UI (Recomendado para pruebas)
- URL: http://localhost:8000/docs
- Interfaz gráfica para probar todas las APIs
- Documentación automática de endpoints

#### Endpoints Principales
- **Health Check**: `GET /health`
- **Información**: `GET /info`
- **Autenticación**: `POST /api/v1/auth/login`
- **Registro**: `POST /api/v1/auth/register`
- **Nodos**: `GET /api/v1/nodos`
- **Transformaciones**: `GET /api/v1/transformaciones`
- **Solicitudes**: `POST /api/v1/solicitudes`
- **Métricas**: `GET /api/v1/metricas`

#### SOAP WSDL
- URL: http://localhost:8000/soap?wsdl
- Servicios SOAP para integración con backend cliente

## Flujo de Trabajo

### 1. Registro y Autenticación
```bash
# Registrar usuario
POST /api/v1/auth/register
{
    "username": "usuario",
    "email": "user@example.com", 
    "password": "password123"
}

# Iniciar sesión
POST /api/v1/auth/login
{
    "username": "usuario",
    "password": "password123"
}
```

### 2. Crear Solicitud de Procesamiento
```bash
# Subir imágenes y definir transformaciones
POST /api/v1/solicitudes
- Archivos: imagenes[]
- Transformaciones: JSON con configuración
- Descripción: texto descriptivo
```

### 3. Monitorear Progreso
```bash
# Ver solicitudes del usuario
GET /api/v1/solicitudes

# Ver solicitud específica
GET /api/v1/solicitudes/{id}

# Descargar imagen procesada
GET /api/v1/imagenes/{id}/download
```

## Estructura del Proyecto

```
distribuidos v2/
├── servidor_aplicacion/           # Servidor principal Python
│   ├── main.py                   # Punto de entrada FastAPI
│   ├── config.py                 # Configuración del servidor
│   ├── models.py                 # Modelos de base de datos
│   ├── schemas.py                # Esquemas Pydantic
│   ├── database.py               # Conexión a BD
│   ├── auth.py                   # Autenticación JWT
│   ├── routes.py                 # Rutas REST API
│   ├── soap_service.py           # Servicio SOAP
│   └── grpc_client.py            # Cliente gRPC
├── nodos/                        # Nodos de procesamiento
│   ├── nodo.py                   # Punto de entrada del nodo
│   ├── config.py                 # Configuración del nodo
│   ├── image_processor.py        # Procesador de imágenes
│   └── grpc_server.py            # Servidor gRPC
├── proto/                        # Definiciones Protocol Buffers
│   └── image_processing.proto    # Esquema gRPC
├── database/                     # Scripts de base de datos
│   └── create_tables.sql         # Script de creación
├── tests/                        # Pruebas del sistema
│   └── test_sistema.py           # Tests automatizados
├── uploads/                      # Imágenes originales
├── processed_images/             # Imágenes procesadas
├── work/                         # Directorio de trabajo de nodos
├── logs/                         # Archivos de log
├── requirements.txt              # Dependencias Python
├── .env                          # Variables de entorno
├── init.bat                      # Script de inicialización
├── start_sistema.bat             # Script de inicio
└── generate_proto.bat            # Generar archivos protobuf
```

## API REST (Swagger)

### Autenticación
- `POST /auth/register` - Registrar usuario
- `POST /auth/login` - Iniciar sesión
- `GET /auth/me` - Información del usuario actual

### Nodos
- `GET /nodos` - Listar nodos
- `POST /nodos` - Registrar nodo
- `PUT /nodos/{id}` - Actualizar nodo
- `GET /nodos/{id}/ping` - Ping a nodo
- `GET /nodos/{id}/status` - Estado del nodo

### Solicitudes
- `POST /solicitudes` - Crear solicitud
- `GET /solicitudes` - Listar solicitudes del usuario
- `GET /solicitudes/{id}` - Obtener solicitud específica
- `POST /solicitudes/{id}/procesar` - Iniciar procesamiento

### Imágenes
- `GET /imagenes/{id}/download` - Descargar imagen

### Sistema
- `GET /transformaciones` - Transformaciones disponibles
- `GET /metricas` - Métricas del sistema
- `GET /health` - Estado del sistema

## Servicios SOAP

### Métodos Disponibles
- `login(username, password)` - Autenticación
- `registrar_usuario(username, email, password)` - Registro
- `crear_solicitud(token, usuario_id, descripcion, imagenes)` - Nueva solicitud
- `obtener_solicitud(solicitud_id)` - Obtener solicitud
- `obtener_solicitudes_usuario(usuario_id)` - Solicitudes del usuario
- `procesar_solicitud(solicitud_id)` - Iniciar procesamiento
- `obtener_nodos()` - Lista de nodos
- `obtener_metricas()` - Métricas del sistema

## Comunicación gRPC

### Servicios del Nodo
- `ProcessImage` - Procesar una imagen
- `GetNodeStatus` - Obtener estado del nodo
- `Ping` - Verificar conectividad

### Tipos de Transformación
- GRAYSCALE, RESIZE, CROP, ROTATE, FLIP
- BLUR, SHARPEN, BRIGHTNESS_CONTRAST
- WATERMARK, CONVERT_FORMAT

## Monitoreo y Logs

### Logs del Sistema
- Servidor: `logs/servidor.log`
- Nodos: `work/logs/{node_id}.log`
- Base de datos: Tabla `logs`

### Métricas Disponibles
- Total de usuarios registrados
- Total de solicitudes procesadas
- Total de imágenes procesadas
- Nodos activos/inactivos
- Estadísticas por nodo

## Desarrollo y Pruebas

### Ejecutar Pruebas
```bash
# Activar entorno virtual
venv\Scripts\activate.bat

# Ejecutar pruebas
python tests\test_sistema.py
```

### Generar Archivos Protobuf
```bash
generate_proto.bat
```

### Variables de Entorno
Editar `.env` para personalizar:
- `DATABASE_URL` - Conexión a MySQL
- `SECRET_KEY` - Clave para JWT
- `HOST` y `PORT` - Configuración del servidor
- `LOG_LEVEL` - Nivel de logging

## Avance 2 - Estado Actual

### ✅ Completado
1. **Arquitectura del sistema** implementada
2. **Base de datos** con todas las tablas necesarias
3. **Servidor de aplicación Python** con FastAPI
4. **Interfaz Swagger** funcionando
5. **Servicios SOAP** implementados
6. **Comunicación gRPC** configurada
7. **Nodos de procesamiento** con hilos
8. **Sistema de autenticación** JWT
9. **Procesamiento de imágenes** con PIL/OpenCV
10. **Mensajes de prueba** para todos los métodos

### 🔄 Para Avance 3
- Integración completa del procesamiento
- Frontend web cliente
- Flujo completo de transformación de imágenes

### 📊 Para Avance 4
- Métricas avanzadas de consumo
- Réplica de base de datos
- Optimizaciones de rendimiento

## Solución de Problemas

### Error de Conexión a MySQL
```bash
# Verificar que MySQL esté corriendo
# Verificar credenciales en .env
# Ejecutar script create_tables.sql
```

### Error de Puertos
```bash
# Verificar que los puertos estén libres
netstat -an | findstr :8000
netstat -an | findstr :50051
```

### Problemas con Dependencias
```bash
# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

## Contacto y Soporte

Para problemas o dudas sobre el sistema, revisar:
1. Logs en el directorio `logs/`
2. Estado del sistema en `/health`
3. Documentación en `/docs`