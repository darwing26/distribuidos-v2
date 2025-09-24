# Configuración de la base de datos
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from servidor_aplicacion.config import Config
from servidor_aplicacion.models import Base
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear el engine de la base de datos
engine = create_engine(
    Config.DATABASE_URL,
    echo=True,  # Para debugging, cambiar a False en producción
    pool_pre_ping=True,
    pool_recycle=300
)

# Crear SessionLocal para las conexiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Crear todas las tablas en la base de datos"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas creadas exitosamente")
    except Exception as e:
        logger.error(f"Error al crear las tablas: {e}")
        raise

def get_db():
    """Obtener una sesión de la base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test de conexión
def test_connection():
    """Probar la conexión a la base de datos"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("Conexión a la base de datos exitosa")
        return True
    except Exception as e:
        logger.error(f"Error de conexión a la base de datos: {e}")
        return False