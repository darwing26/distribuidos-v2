# Modelos de datos con SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Boolean, BigInteger, Enum, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class EstadoNodo(enum.Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    ERROR = "error"

class EstadoSolicitud(enum.Enum):
    PENDIENTE = "pendiente"
    PROCESANDO = "procesando"
    COMPLETADO = "completado"
    ERROR = "error"

class EstadoImagen(enum.Enum):
    PENDIENTE = "pendiente"
    PROCESANDO = "procesando"
    COMPLETADO = "completado"
    ERROR = "error"

class NivelLog(enum.Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    fecha_registro = Column(TIMESTAMP, default=datetime.utcnow)
    activo = Column(Boolean, default=True)
    
    # Relaciones
    solicitudes = relationship("Solicitud", back_populates="usuario")

class Nodo(Base):
    __tablename__ = "nodos"
    
    id = Column(Integer, primary_key=True, index=True)
    identificador = Column(String(50), unique=True, index=True, nullable=False)
    direccion_ip = Column(String(45), nullable=False)
    puerto = Column(Integer, nullable=False)
    estado = Column(Enum(EstadoNodo), default=EstadoNodo.INACTIVO)
    fecha_registro = Column(TIMESTAMP, default=datetime.utcnow)
    ultima_actualizacion = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    descripcion = Column(Text)
    
    # Relaciones
    imagenes = relationship("Imagen", back_populates="nodo")

class Solicitud(Base):
    __tablename__ = "solicitudes"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    fecha_solicitud = Column(TIMESTAMP, default=datetime.utcnow)
    estado = Column(Enum(EstadoSolicitud), default=EstadoSolicitud.PENDIENTE)
    total_imagenes = Column(Integer, default=0)
    imagenes_procesadas = Column(Integer, default=0)
    fecha_completado = Column(TIMESTAMP)
    descripcion = Column(Text)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="solicitudes")
    imagenes = relationship("Imagen", back_populates="solicitud")

class Transformacion(Base):
    __tablename__ = "transformaciones"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, index=True, nullable=False)
    descripcion = Column(Text)
    parametros_schema = Column(JSON)
    activo = Column(Boolean, default=True)

class Imagen(Base):
    __tablename__ = "imagenes"
    
    id = Column(Integer, primary_key=True, index=True)
    solicitud_id = Column(Integer, ForeignKey("solicitudes.id", ondelete="CASCADE"), nullable=False)
    nombre_original = Column(String(255), nullable=False)
    ruta_original = Column(String(500), nullable=False)
    ruta_procesada = Column(String(500))
    formato_original = Column(String(10))
    formato_destino = Column(String(10))
    tamaño_original = Column(BigInteger)
    tamaño_procesado = Column(BigInteger)
    fecha_recepcion = Column(TIMESTAMP, default=datetime.utcnow)
    fecha_inicio_procesamiento = Column(TIMESTAMP)
    fecha_fin_procesamiento = Column(TIMESTAMP)
    nodo_id = Column(Integer, ForeignKey("nodos.id", ondelete="SET NULL"))
    estado = Column(Enum(EstadoImagen), default=EstadoImagen.PENDIENTE)
    transformaciones_solicitadas = Column(JSON)
    transformaciones_aplicadas = Column(JSON)
    mensaje_error = Column(Text)
    
    # Relaciones
    solicitud = relationship("Solicitud", back_populates="imagenes")
    nodo = relationship("Nodo", back_populates="imagenes")

class Log(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    nivel = Column(Enum(NivelLog), nullable=False)
    mensaje = Column(Text, nullable=False)
    modulo = Column(String(100))
    funcion = Column(String(100))
    linea = Column(Integer)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"))
    solicitud_id = Column(Integer, ForeignKey("solicitudes.id", ondelete="SET NULL"))
    imagen_id = Column(Integer, ForeignKey("imagenes.id", ondelete="SET NULL"))
    nodo_id = Column(Integer, ForeignKey("nodos.id", ondelete="SET NULL"))
    datos_adicionales = Column(JSON)