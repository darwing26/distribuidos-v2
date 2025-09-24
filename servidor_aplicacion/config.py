# Configuración del proyecto
import os

class Config:
    # Base de datos (SQLite para desarrollo si no hay MySQL)
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test_sistema.db")
    
    # Servidor
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    
    # Seguridad
    SECRET_KEY = os.getenv("SECRET_KEY", "tu-clave-secreta-muy-segura-cambiala-en-produccion")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Directorios
    UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
    PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "processed_images")
    LOGS_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
    
    # gRPC Nodos
    NODO_TIMEOUT = 30
    
    # Límites
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    @classmethod
    def create_directories(cls):
        """Crear directorios necesarios si no existen"""
        for directory in [cls.UPLOAD_DIR, cls.PROCESSED_DIR, cls.LOGS_DIR]:
            os.makedirs(directory, exist_ok=True)