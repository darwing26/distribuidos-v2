# Servidor SOAP para comunicación con el backend cliente
from spyne import Application, rpc, ServiceBase, Integer, Unicode, ComplexModel, Array, Boolean, DateTime, Float
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from spyne.model.fault import Fault
from typing import List, Dict, Any
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from servidor_aplicacion.database import get_db
from servidor_aplicacion.models import Usuario, Solicitud, Imagen, Nodo, Log
from servidor_aplicacion.schemas import EstadoSolicitud, EstadoImagen, NivelLog
from servidor_aplicacion.auth import authenticate_user, create_access_token
from servidor_aplicacion.grpc_client import grpc_client

logger = logging.getLogger(__name__)

# Modelos complejos para SOAP
class UsuarioSOAP(ComplexModel):
    id = Integer
    username = Unicode
    email = Unicode
    fecha_registro = DateTime
    activo = Boolean

class TransformacionSOAP(ComplexModel):
    tipo = Unicode
    parametros = Unicode  # JSON serializado

class ImagenSOAP(ComplexModel):
    id = Integer
    nombre_original = Unicode
    estado = Unicode
    transformaciones_solicitadas = Array(TransformacionSOAP)
    fecha_recepcion = DateTime
    fecha_fin_procesamiento = DateTime
    mensaje_error = Unicode

class SolicitudSOAP(ComplexModel):
    id = Integer
    usuario_id = Integer
    fecha_solicitud = DateTime
    estado = Unicode
    total_imagenes = Integer
    imagenes_procesadas = Integer
    descripcion = Unicode
    imagenes = Array(ImagenSOAP)

class NodoSOAP(ComplexModel):
    id = Integer
    identificador = Unicode
    direccion_ip = Unicode
    puerto = Integer
    estado = Unicode
    descripcion = Unicode

class RespuestaSOAP(ComplexModel):
    success = Boolean
    mensaje = Unicode
    datos = Unicode  # JSON serializado

class TokenSOAP(ComplexModel):
    access_token = Unicode
    token_type = Unicode
    expires_in = Integer

class MetricasSOAP(ComplexModel):
    total_usuarios = Integer
    total_solicitudes = Integer
    total_imagenes_procesadas = Integer
    nodos_activos = Integer
    uptime = Unicode

# Servicio SOAP principal
class ImageProcessingService(ServiceBase):
    
    @rpc(Unicode, Unicode, _returns=TokenSOAP)
    def login(ctx, username, password):
        """Autenticación de usuario"""
        try:
            db = next(get_db())
            user = authenticate_user(db, username, password)
            
            if not user:
                raise Fault("AuthenticationError", "Credenciales inválidas")
            
            access_token = create_access_token(data={"sub": user.username})
            
            return TokenSOAP(
                access_token=access_token,
                token_type="bearer",
                expires_in=1800  # 30 minutos
            )
            
        except Exception as e:
            logger.error(f"Error en login SOAP: {e}")
            raise Fault("InternalError", str(e))
    
    @rpc(Unicode, Unicode, Unicode, _returns=UsuarioSOAP)
    def registrar_usuario(ctx, username, email, password):
        """Registrar un nuevo usuario"""
        try:
            from .auth import get_password_hash
            
            db = next(get_db())
            
            # Verificar si el usuario ya existe
            existing_user = db.query(Usuario).filter(
                (Usuario.username == username) | (Usuario.email == email)
            ).first()
            
            if existing_user:
                raise Fault("UserExists", "El usuario o email ya existe")
            
            # Crear nuevo usuario
            hashed_password = get_password_hash(password)
            new_user = Usuario(
                username=username,
                email=email,
                password_hash=hashed_password
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            return UsuarioSOAP(
                id=new_user.id,
                username=new_user.username,
                email=new_user.email,
                fecha_registro=new_user.fecha_registro,
                activo=new_user.activo
            )
            
        except Exception as e:
            logger.error(f"Error en registro SOAP: {e}")
            raise Fault("InternalError", str(e))
    
    @rpc(Unicode, Integer, Unicode, Array(Unicode), _returns=SolicitudSOAP)
    def crear_solicitud(ctx, token, usuario_id, descripcion, nombres_imagenes):
        """Crear una nueva solicitud de procesamiento"""
        try:
            # Aquí deberías validar el token JWT
            # Por simplicidad, asumimos que es válido
            
            db = next(get_db())
            
            # Crear nueva solicitud
            nueva_solicitud = Solicitud(
                usuario_id=usuario_id,
                descripcion=descripcion,
                total_imagenes=len(nombres_imagenes),
                estado=EstadoSolicitud.PENDIENTE
            )
            
            db.add(nueva_solicitud)
            db.commit()
            db.refresh(nueva_solicitud)
            
            # Crear registros de imágenes
            imagenes = []
            for nombre in nombres_imagenes:
                imagen = Imagen(
                    solicitud_id=nueva_solicitud.id,
                    nombre_original=nombre,
                    ruta_original=f"/uploads/{nombre}",  # Ruta por defecto
                    formato_original="jpg",  # Por defecto
                    tamaño_original=0,  # Se actualizará después
                    estado=EstadoImagen.PENDIENTE
                )
                db.add(imagen)
                imagenes.append(imagen)
            
            db.commit()
            
            # Crear respuesta
            imagenes_soap = []
            for img in imagenes:
                img_soap = ImagenSOAP(
                    id=img.id,
                    nombre_original=img.nombre_original,
                    estado=img.estado.value,
                    fecha_recepcion=img.fecha_recepcion
                )
                imagenes_soap.append(img_soap)
            
            return SolicitudSOAP(
                id=nueva_solicitud.id,
                usuario_id=nueva_solicitud.usuario_id,
                fecha_solicitud=nueva_solicitud.fecha_solicitud,
                estado=nueva_solicitud.estado.value,
                total_imagenes=nueva_solicitud.total_imagenes,
                imagenes_procesadas=nueva_solicitud.imagenes_procesadas,
                descripcion=nueva_solicitud.descripcion,
                imagenes=imagenes_soap
            )
            
        except Exception as e:
            logger.error(f"Error al crear solicitud SOAP: {e}")
            raise Fault("InternalError", str(e))
    
    @rpc(Integer, _returns=SolicitudSOAP)
    def obtener_solicitud(ctx, solicitud_id):
        """Obtener una solicitud por ID"""
        try:
            db = next(get_db())
            
            solicitud = db.query(Solicitud).filter(Solicitud.id == solicitud_id).first()
            if not solicitud:
                raise Fault("NotFound", "Solicitud no encontrada")
            
            # Convertir a SOAP
            imagenes_soap = []
            for img in solicitud.imagenes:
                img_soap = ImagenSOAP(
                    id=img.id,
                    nombre_original=img.nombre_original,
                    estado=img.estado.value,
                    fecha_recepcion=img.fecha_recepcion,
                    fecha_fin_procesamiento=img.fecha_fin_procesamiento,
                    mensaje_error=img.mensaje_error
                )
                imagenes_soap.append(img_soap)
            
            return SolicitudSOAP(
                id=solicitud.id,
                usuario_id=solicitud.usuario_id,
                fecha_solicitud=solicitud.fecha_solicitud,
                estado=solicitud.estado.value,
                total_imagenes=solicitud.total_imagenes,
                imagenes_procesadas=solicitud.imagenes_procesadas,
                descripcion=solicitud.descripcion,
                imagenes=imagenes_soap
            )
            
        except Exception as e:
            logger.error(f"Error al obtener solicitud SOAP: {e}")
            raise Fault("InternalError", str(e))
    
    @rpc(Integer, _returns=Array(SolicitudSOAP))
    def obtener_solicitudes_usuario(ctx, usuario_id):
        """Obtener todas las solicitudes de un usuario"""
        try:
            db = next(get_db())
            
            solicitudes = db.query(Solicitud).filter(Solicitud.usuario_id == usuario_id).all()
            
            solicitudes_soap = []
            for solicitud in solicitudes:
                solicitud_soap = SolicitudSOAP(
                    id=solicitud.id,
                    usuario_id=solicitud.usuario_id,
                    fecha_solicitud=solicitud.fecha_solicitud,
                    estado=solicitud.estado.value,
                    total_imagenes=solicitud.total_imagenes,
                    imagenes_procesadas=solicitud.imagenes_procesadas,
                    descripcion=solicitud.descripcion
                )
                solicitudes_soap.append(solicitud_soap)
            
            return solicitudes_soap
            
        except Exception as e:
            logger.error(f"Error al obtener solicitudes del usuario SOAP: {e}")
            raise Fault("InternalError", str(e))
    
    @rpc(Integer, _returns=RespuestaSOAP)
    def procesar_solicitud(ctx, solicitud_id):
        """Iniciar el procesamiento de una solicitud"""
        try:
            db = next(get_db())
            
            solicitud = db.query(Solicitud).filter(Solicitud.id == solicitud_id).first()
            if not solicitud:
                raise Fault("NotFound", "Solicitud no encontrada")
            
            # Obtener nodos disponibles
            nodos_activos = db.query(Nodo).filter(Nodo.estado == 'activo').all()
            if not nodos_activos:
                raise Fault("NoNodesAvailable", "No hay nodos disponibles")
            
            # Actualizar estado de la solicitud
            solicitud.estado = EstadoSolicitud.PROCESANDO
            db.commit()
            
            # Aquí se implementaría la lógica de procesamiento asíncrono
            # Por ahora, simulamos una respuesta exitosa
            
            return RespuestaSOAP(
                success=True,
                mensaje=f"Procesamiento iniciado para solicitud {solicitud_id}",
                datos=f'{{"solicitud_id": {solicitud_id}, "nodos_asignados": {len(nodos_activos)}}}'
            )
            
        except Exception as e:
            logger.error(f"Error al procesar solicitud SOAP: {e}")
            raise Fault("InternalError", str(e))
    
    @rpc(_returns=Array(NodoSOAP))
    def obtener_nodos(ctx):
        """Obtener la lista de nodos registrados"""
        try:
            db = next(get_db())
            
            nodos = db.query(Nodo).all()
            nodos_soap = []
            
            for nodo in nodos:
                nodo_soap = NodoSOAP(
                    id=nodo.id,
                    identificador=nodo.identificador,
                    direccion_ip=nodo.direccion_ip,
                    puerto=nodo.puerto,
                    estado=nodo.estado.value,
                    descripcion=nodo.descripcion
                )
                nodos_soap.append(nodo_soap)
            
            return nodos_soap
            
        except Exception as e:
            logger.error(f"Error al obtener nodos SOAP: {e}")
            raise Fault("InternalError", str(e))
    
    @rpc(_returns=MetricasSOAP)
    def obtener_metricas(ctx):
        """Obtener métricas del sistema"""
        try:
            db = next(get_db())
            
            total_usuarios = db.query(Usuario).count()
            total_solicitudes = db.query(Solicitud).count()
            total_imagenes_procesadas = db.query(Imagen).filter(
                Imagen.estado == EstadoImagen.COMPLETADO
            ).count()
            nodos_activos = db.query(Nodo).filter(Nodo.estado == 'activo').count()
            
            return MetricasSOAP(
                total_usuarios=total_usuarios,
                total_solicitudes=total_solicitudes,
                total_imagenes_procesadas=total_imagenes_procesadas,
                nodos_activos=nodos_activos,
                uptime="Sistema en funcionamiento"
            )
            
        except Exception as e:
            logger.error(f"Error al obtener métricas SOAP: {e}")
            raise Fault("InternalError", str(e))

# Configuración de la aplicación SOAP
application = Application(
    [ImageProcessingService],
    tns='http://sistema.imagenes.soap',
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11()
)

# Crear aplicación WSGI
soap_application = WsgiApplication(application)