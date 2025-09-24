# Configuración del nodo de procesamiento
import os
import logging
from typing import Dict, Any

class NodoConfig:
    # Identificación del nodo
    NODE_ID = os.getenv("NODE_ID", "nodo-001")
    NODE_DESCRIPTION = os.getenv("NODE_DESCRIPTION", "Nodo de procesamiento de imágenes")
    
    # Red
    GRPC_HOST = os.getenv("GRPC_HOST", "0.0.0.0")
    GRPC_PORT = int(os.getenv("GRPC_PORT", 50051))
    
    # Directorios de trabajo
    WORK_DIR = os.path.join(os.path.dirname(__file__), "..", "work")
    INPUT_DIR = os.path.join(WORK_DIR, "input")
    OUTPUT_DIR = os.path.join(WORK_DIR, "output")
    TEMP_DIR = os.path.join(WORK_DIR, "temp")
    LOG_DIR = os.path.join(WORK_DIR, "logs")
    
    # Configuración de procesamiento
    MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", 4))
    MAX_IMAGE_SIZE = 100 * 1024 * 1024  # 100MB
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    # Timeouts
    PROCESSING_TIMEOUT = int(os.getenv("PROCESSING_TIMEOUT", 300))  # 5 minutos
    HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", 30))  # 30 segundos
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def create_directories(cls):
        """Crear directorios necesarios"""
        for directory in [cls.WORK_DIR, cls.INPUT_DIR, cls.OUTPUT_DIR, cls.TEMP_DIR, cls.LOG_DIR]:
            os.makedirs(directory, exist_ok=True)
    
    @classmethod
    def setup_logging(cls):
        """Configurar el sistema de logging"""
        cls.create_directories()
        
        log_file = os.path.join(cls.LOG_DIR, f"{cls.NODE_ID}.log")
        
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        return logging.getLogger(cls.NODE_ID)