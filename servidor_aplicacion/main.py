# Servidor principal - FastAPI + SOAP
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
# from fastapi.middleware.wsgi import WSGIMiddleware
import logging
import uvicorn
from contextlib import asynccontextmanager

# Imports locales
from servidor_aplicacion.config import Config
from servidor_aplicacion.database import create_tables, test_connection
from servidor_aplicacion.routes import router as api_router
# from servidor_aplicacion.soap_service import soap_application

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eventos de inicio y cierre del servidor"""
    # Startup
    logger.info("Iniciando servidor de aplicación...")
    
    # Crear directorios necesarios
    Config.create_directories()
    
    # Probar conexión a la base de datos
    if not test_connection():
        logger.error("No se pudo conectar a la base de datos")
        raise Exception("Error de conexión a la base de datos")
    
    # Crear tablas si no existen
    try:
        create_tables()
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}")
    
    logger.info("Servidor iniciado correctamente")
    yield
    
    # Shutdown
    logger.info("Cerrando servidor...")

# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema de Procesamiento de Imágenes",
    description="API REST para el sistema distribuido de procesamiento de imágenes",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas de la API REST
app.include_router(api_router, prefix="/api/v1")

# Montar el servicio SOAP (comentado temporalmente)
# app.mount("/soap", WSGIMiddleware(soap_application))

# Rutas principales
@app.get("/")
async def root():
    """Página principal del servidor"""
    return {
        "message": "Sistema de Procesamiento de Imágenes - Servidor de Aplicación",
        "version": "1.0.0",
        "swagger_ui": "/docs",
        "soap_wsdl": "/soap?wsdl",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud del servidor"""
    return {
        "status": "healthy",
        "database": "connected" if test_connection() else "disconnected",
        "services": {
            "rest_api": "active",
            "soap_service": "active"
        }
    }

@app.get("/info")
async def server_info():
    """Información del servidor y servicios disponibles"""
    return {
        "server": "Sistema de Procesamiento de Imágenes",
        "version": "1.0.0",
        "protocols": {
            "rest": {
                "endpoint": "/api/v1",
                "documentation": "/docs"
            },
            "soap": {
                "endpoint": "/soap",
                "wsdl": "/soap?wsdl"
            }
        },
        "features": [
            "Registro y autenticación de usuarios",
            "Gestión de solicitudes de procesamiento",
            "Comunicación gRPC con nodos",
            "Métricas del sistema",
            "Interfaz Swagger para pruebas"
        ]
    }

if __name__ == "__main__":
    logger.info(f"Iniciando servidor en {Config.HOST}:{Config.PORT}")
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=True,  # Solo para desarrollo
        log_level="info"
    )