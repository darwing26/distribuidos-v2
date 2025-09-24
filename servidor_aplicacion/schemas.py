# Esquemas de Pydantic para validación de datos
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Enums para validación
class EstadoNodo(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    ERROR = "error"

class EstadoSolicitud(str, Enum):
    PENDIENTE = "pendiente"
    PROCESANDO = "procesando"
    COMPLETADO = "completado"
    ERROR = "error"

class EstadoImagen(str, Enum):
    PENDIENTE = "pendiente"
    PROCESANDO = "procesando"
    COMPLETADO = "completado"
    ERROR = "error"

class NivelLog(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

# Esquemas de Usuario
class UsuarioBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=6)

class UsuarioLogin(BaseModel):
    username: str
    password: str

class Usuario(UsuarioBase):
    id: int
    fecha_registro: datetime
    activo: bool
    
    class Config:
        from_attributes = True

# Esquemas de Token
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Esquemas de Nodo
class NodoBase(BaseModel):
    identificador: str = Field(..., min_length=1, max_length=50)
    direccion_ip: str = Field(..., pattern=r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')
    puerto: int = Field(..., ge=1, le=65535)
    descripcion: Optional[str] = None

class NodoCreate(NodoBase):
    pass

class NodoUpdate(BaseModel):
    estado: EstadoNodo
    descripcion: Optional[str] = None

class Nodo(NodoBase):
    id: int
    estado: EstadoNodo
    fecha_registro: datetime
    ultima_actualizacion: datetime
    
    class Config:
        from_attributes = True

# Esquemas de Transformación
class TransformacionBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=50)
    descripcion: Optional[str] = None
    parametros_schema: Optional[Dict[str, Any]] = None

class TransformacionCreate(TransformacionBase):
    pass

class Transformacion(TransformacionBase):
    id: int
    activo: bool
    
    class Config:
        from_attributes = True

# Esquemas de parámetros de transformación
class ParametrosRedimensionar(BaseModel):
    width: int = Field(..., ge=1)
    height: int = Field(..., ge=1)
    mantener_aspecto: bool = True

class ParametrosRecortar(BaseModel):
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    width: int = Field(..., ge=1)
    height: int = Field(..., ge=1)

class ParametrosRotar(BaseModel):
    angulo: float

class ParametrosReflejar(BaseModel):
    horizontal: bool = False
    vertical: bool = False

class ParametrosDesenfocar(BaseModel):
    radio: float = Field(..., ge=0.1, le=10.0)

class ParametrosNitidez(BaseModel):
    factor: float = Field(..., ge=0.1, le=3.0)

class ParametrosBrilloContraste(BaseModel):
    brillo: float = Field(..., ge=-100, le=100)
    contraste: float = Field(..., ge=-100, le=100)

class ParametrosMarcaAgua(BaseModel):
    texto: str
    posicion: str = Field(..., pattern=r'^(top-left|top-right|bottom-left|bottom-right|center)$')
    tamaño: int = Field(..., ge=8, le=72)
    color: str = Field(..., pattern=r'^#[0-9a-fA-F]{6}$')

class ParametrosConvertirFormato(BaseModel):
    formato: str = Field(..., pattern=r'^(jpg|jpeg|png|bmp|tiff|tif)$')

# Esquema de transformación solicitada
class TransformacionSolicitada(BaseModel):
    tipo: str = Field(..., pattern=r'^(escala_grises|redimensionar|recortar|rotar|reflejar|desenfocar|nitidez|brillo_contraste|marca_agua|convertir_formato)$')
    parametros: Optional[Dict[str, Any]] = {}

# Esquemas de Imagen
class ImagenBase(BaseModel):
    nombre_original: str
    transformaciones_solicitadas: List[TransformacionSolicitada] = []

class ImagenCreate(ImagenBase):
    solicitud_id: int
    ruta_original: str
    formato_original: str
    tamaño_original: int

class Imagen(ImagenBase):
    id: int
    solicitud_id: int
    ruta_original: str
    ruta_procesada: Optional[str] = None
    formato_original: str
    formato_destino: Optional[str] = None
    tamaño_original: int
    tamaño_procesado: Optional[int] = None
    fecha_recepcion: datetime
    fecha_inicio_procesamiento: Optional[datetime] = None
    fecha_fin_procesamiento: Optional[datetime] = None
    nodo_id: Optional[int] = None
    estado: EstadoImagen
    transformaciones_aplicadas: Optional[Dict[str, Any]] = None
    mensaje_error: Optional[str] = None
    
    class Config:
        from_attributes = True

# Esquemas de Solicitud
class SolicitudBase(BaseModel):
    descripcion: Optional[str] = None

class SolicitudCreate(SolicitudBase):
    imagenes: List[ImagenBase] = Field(..., min_items=1)

class Solicitud(SolicitudBase):
    id: int
    usuario_id: int
    fecha_solicitud: datetime
    estado: EstadoSolicitud
    total_imagenes: int
    imagenes_procesadas: int
    fecha_completado: Optional[datetime] = None
    imagenes: List[Imagen] = []
    
    class Config:
        from_attributes = True

# Esquemas de Log
class LogBase(BaseModel):
    nivel: NivelLog
    mensaje: str
    modulo: Optional[str] = None
    funcion: Optional[str] = None
    linea: Optional[int] = None

class LogCreate(LogBase):
    usuario_id: Optional[int] = None
    solicitud_id: Optional[int] = None
    imagen_id: Optional[int] = None
    nodo_id: Optional[int] = None
    datos_adicionales: Optional[Dict[str, Any]] = None

class Log(LogBase):
    id: int
    timestamp: datetime
    usuario_id: Optional[int] = None
    solicitud_id: Optional[int] = None
    imagen_id: Optional[int] = None
    nodo_id: Optional[int] = None
    datos_adicionales: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

# Esquemas de respuesta
class RespuestaBase(BaseModel):
    success: bool
    mensaje: str
    datos: Optional[Any] = None

class RespuestaError(BaseModel):
    success: bool = False
    error: str
    detalles: Optional[str] = None

# Esquemas para métricas
class MetricasNodo(BaseModel):
    nodo_id: int
    imagenes_procesadas: int
    tiempo_promedio_procesamiento: float
    errores: int
    estado: EstadoNodo

class MetricasSistema(BaseModel):
    total_usuarios: int
    total_solicitudes: int
    total_imagenes_procesadas: int
    nodos_activos: int
    nodos: List[MetricasNodo]