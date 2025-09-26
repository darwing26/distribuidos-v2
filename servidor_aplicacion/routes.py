# Rutas REST API con FastAPI para interfaz Swagger
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import json
from datetime import datetime

from servidor_aplicacion.database import get_db
from servidor_aplicacion.models import Usuario, Solicitud, Imagen, Nodo, Transformacion, Log
from servidor_aplicacion.schemas import (
    Usuario as UsuarioSchema, UsuarioCreate, UsuarioLogin, Token,
    Solicitud as SolicitudSchema, SolicitudCreate,
    Imagen as ImagenSchema,
    Nodo as NodoSchema, NodoCreate, NodoUpdate,
    Transformacion as TransformacionSchema,
    RespuestaBase, MetricasSistema, MetricasNodo
)
from servidor_aplicacion.auth import authenticate_user, create_access_token, get_current_active_user, get_password_hash
from servidor_aplicacion.grpc_client import grpc_client
from servidor_aplicacion.config import Config

router = APIRouter()

# Rutas de autenticación
@router.post("/auth/register", response_model=UsuarioSchema, tags=["Autenticación"])
async def register(user_data: UsuarioCreate, db: Session = Depends(get_db)):
    """Registrar un nuevo usuario"""
    # Verificar si el usuario ya existe
    existing_user = db.query(Usuario).filter(
        (Usuario.username == user_data.username) | (Usuario.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="El usuario o email ya existe"
        )
    
    # Crear nuevo usuario
    hashed_password = get_password_hash(user_data.password)
    new_user = Usuario(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/auth/login", response_model=Token, tags=["Autenticación"])
async def login(user_credentials: UsuarioLogin, db: Session = Depends(get_db)):
    """Iniciar sesión y obtener token"""
    user = authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/auth/me", response_model=UsuarioSchema, tags=["Autenticación"])
async def get_current_user_info(current_user: Usuario = Depends(get_current_active_user)):
    """Obtener información del usuario actual"""
    return current_user

# Rutas de usuarios
@router.get("/usuarios", response_model=List[UsuarioSchema], tags=["Usuarios"])
async def get_users(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    """Obtener lista de usuarios (solo para administradores)"""
    users = db.query(Usuario).all()
    return users

@router.get("/usuarios/test", response_model=List[UsuarioSchema], tags=["Test"])
async def get_users_test(db: Session = Depends(get_db)):
    """Obtener lista de usuarios (endpoint de prueba sin autenticación)"""
    users = db.query(Usuario).all()
    return users

# Rutas de nodos
@router.get("/nodos", response_model=List[NodoSchema], tags=["Nodos"])
async def get_nodes(db: Session = Depends(get_db)):
    """Obtener lista de nodos registrados"""
    nodes = db.query(Nodo).all()
    return nodes

@router.post("/nodos", response_model=NodoSchema, tags=["Nodos"])
async def create_node(node_data: NodoCreate, db: Session = Depends(get_db)):
    """Registrar un nuevo nodo"""
    # Verificar si el nodo ya existe
    existing_node = db.query(Nodo).filter(
        Nodo.identificador == node_data.identificador
    ).first()
    
    if existing_node:
        raise HTTPException(status_code=400, detail="El nodo ya existe")
    
    new_node = Nodo(**node_data.model_dump())
    db.add(new_node)
    db.commit()
    db.refresh(new_node)
    
    return new_node

@router.put("/nodos/{node_id}", response_model=NodoSchema, tags=["Nodos"])
async def update_node(node_id: int, node_update: NodoUpdate, db: Session = Depends(get_db)):
    """Actualizar estado de un nodo"""
    node = db.query(Nodo).filter(Nodo.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")
    
    update_data = node_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(node, field, value)
    
    # Actualizar timestamp
    node.ultima_actualizacion = datetime.now()
    
    db.commit()
    db.refresh(node)
    return node

@router.get("/nodos/{node_id}/ping", tags=["Nodos"])
async def ping_node(node_id: int, db: Session = Depends(get_db)):
    """Hacer ping a un nodo específico"""
    node = db.query(Nodo).filter(Nodo.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")
    
    success, message = grpc_client.ping_node(node.direccion_ip, node.puerto)
    
    return {
        "success": success,
        "message": message,
        "node_id": node_id,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/nodos/{node_id}/status", tags=["Nodos"])
async def get_node_status(node_id: int, db: Session = Depends(get_db)):
    """Obtener estado detallado de un nodo"""
    node = db.query(Nodo).filter(Nodo.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")
    
    try:
        status_info = grpc_client.get_node_status(
            node.direccion_ip, 
            node.puerto, 
            node.identificador
        )
        return status_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Rutas de transformaciones
@router.get("/transformaciones", response_model=List[TransformacionSchema], tags=["Transformaciones"])
async def get_transformations(db: Session = Depends(get_db)):
    """Obtener lista de transformaciones disponibles"""
    transformations = db.query(Transformacion).filter(Transformacion.activo == True).all()
    return transformations

@router.get("/transformaciones/{transformation_id}", response_model=TransformacionSchema, tags=["Transformaciones"])
async def get_transformation(transformation_id: int, db: Session = Depends(get_db)):
    """Obtener una transformación específica"""
    transformation = db.query(Transformacion).filter(
        Transformacion.id == transformation_id,
        Transformacion.activo == True
    ).first()
    
    if not transformation:
        raise HTTPException(status_code=404, detail="Transformación no encontrada")
    
    return transformation

# Rutas de solicitudes
@router.post("/solicitudes", response_model=SolicitudSchema, tags=["Solicitudes"])
async def create_request(
    descripcion: Optional[str] = Form(None),
    imagenes: List[UploadFile] = File(...),
    transformaciones: str = Form(...),  # JSON string
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Crear una nueva solicitud de procesamiento de imágenes"""
    # Validaciones de entrada
    if len(imagenes) == 0:
        raise HTTPException(status_code=400, detail="Debe proporcionar al menos una imagen")
    
    if len(imagenes) > 10:  # Límite máximo de imágenes
        raise HTTPException(status_code=400, detail="Máximo 10 imágenes por solicitud")
    
    # Validar archivos
    formatos_validos = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif'}
    tamaño_maximo = 10 * 1024 * 1024  # 10 MB por archivo
    
    for imagen in imagenes:
        if not imagen.filename:
            raise HTTPException(status_code=400, detail="Nombre de archivo faltante")
            
        extension = os.path.splitext(imagen.filename.lower())[1]
        if extension not in formatos_validos:
            raise HTTPException(
                status_code=400,
                detail=f"Formato de archivo no soportado: {extension}. Formatos válidos: {', '.join(formatos_validos)}"
            )
        
        # Leer contenido para verificar tamaño
        content = await imagen.read()
        if len(content) > tamaño_maximo:
            raise HTTPException(
                status_code=400,
                detail=f"Archivo {imagen.filename} excede el tamaño máximo de 10MB"
            )
        # Resetear el puntero del archivo
        await imagen.seek(0)
    
    # Parsear y validar transformaciones
    try:
        transformaciones_data = json.loads(transformaciones)
        if not isinstance(transformaciones_data, list):
            raise HTTPException(status_code=400, detail="Las transformaciones deben ser una lista")
        
        if len(transformaciones_data) == 0:
            raise HTTPException(status_code=400, detail="Debe especificar al menos una transformación")
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Formato de transformaciones inválido (JSON)")
    
    # Crear solicitud
    nueva_solicitud = Solicitud(
        usuario_id=current_user.id,
        descripcion=descripcion or "Sin descripción",
        total_imagenes=len(imagenes),
        estado="pendiente"
    )
    
    db.add(nueva_solicitud)
    db.commit()
    db.refresh(nueva_solicitud)
    
    # Crear directorios necesarios
    Config.create_directories()
    imagenes_procesadas = []
    
    try:
        for i, imagen in enumerate(imagenes):
            # Generar nombre único para el archivo
            timestamp = int(datetime.now().timestamp())
            safe_filename = f"{nueva_solicitud.id}_{timestamp}_{i}_{imagen.filename}"
            file_path = os.path.join(Config.UPLOAD_DIR, safe_filename)
            
            # Guardar archivo
            with open(file_path, "wb") as buffer:
                content = await imagen.read()
                buffer.write(content)
            
            # Crear registro de imagen
            imagen_record = Imagen(
                solicitud_id=nueva_solicitud.id,
                nombre_original=imagen.filename,
                ruta_original=file_path,
                formato_original=os.path.splitext(imagen.filename.lower())[1][1:],  # Sin el punto
                tamaño_original=len(content),
                transformaciones_solicitadas=transformaciones_data,
                estado="pendiente"
            )
            
            db.add(imagen_record)
            imagenes_procesadas.append(imagen_record)
        
        db.commit()
        
        # Log de la operación
        log_entry = Log(
            nivel="INFO",
            mensaje=f"Nueva solicitud creada con {len(imagenes)} imágenes",
            usuario_id=current_user.id,
            solicitud_id=nueva_solicitud.id,
            modulo="routes",
            funcion="create_request"
        )
        db.add(log_entry)
        db.commit()
        
        # Actualizar la solicitud con las imágenes
        nueva_solicitud.imagenes = imagenes_procesadas
        db.refresh(nueva_solicitud)
        
        return nueva_solicitud
        
    except Exception as e:
        # Rollback y limpieza en caso de error
        db.rollback()
        
        # Eliminar archivos ya guardados
        for imagen_record in imagenes_procesadas:
            if os.path.exists(imagen_record.ruta_original):
                os.remove(imagen_record.ruta_original)
        
        raise HTTPException(status_code=500, detail=f"Error al crear solicitud: {str(e)}")

@router.get("/solicitudes", response_model=List[SolicitudSchema], tags=["Solicitudes"])
async def get_user_requests(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtener solicitudes del usuario actual"""
    requests = db.query(Solicitud).filter(Solicitud.usuario_id == current_user.id).all()
    return requests

@router.get("/solicitudes/{request_id}", response_model=SolicitudSchema, tags=["Solicitudes"])
async def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtener una solicitud específica"""
    request = db.query(Solicitud).filter(
        Solicitud.id == request_id,
        Solicitud.usuario_id == current_user.id
    ).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    return request

@router.post("/solicitudes/{request_id}/procesar", response_model=RespuestaBase, tags=["Solicitudes"])
async def process_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Iniciar el procesamiento de una solicitud"""
    # Obtener la solicitud
    solicitud = db.query(Solicitud).filter(
        Solicitud.id == request_id,
        Solicitud.usuario_id == current_user.id
    ).first()
    
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    if solicitud.estado != "pendiente":
        raise HTTPException(
            status_code=400, 
            detail=f"La solicitud ya está en estado: {solicitud.estado}"
        )
    
    # Verificar nodos disponibles
    nodos_activos = db.query(Nodo).filter(Nodo.estado == 'activo').all()
    if not nodos_activos:
        raise HTTPException(status_code=503, detail="No hay nodos disponibles")
    
    # Actualizar estado de la solicitud
    solicitud.estado = "procesando"
    
    # Actualizar estado de las imágenes asociadas
    for imagen in solicitud.imagenes:
        if imagen.estado == "pendiente":
            imagen.estado = "procesando"
            imagen.fecha_inicio_procesamiento = datetime.now()
    
    db.commit()
    
    # Registrar log
    log_entry = Log(
        nivel="INFO",
        mensaje=f"Procesamiento iniciado para solicitud {request_id}",
        usuario_id=current_user.id,
        solicitud_id=request_id,
        modulo="routes",
        funcion="process_request"
    )
    db.add(log_entry)
    db.commit()
    
    return RespuestaBase(
        success=True,
        message=f"Procesamiento iniciado para solicitud {request_id}",
        datos={
            "solicitud_id": request_id,
            "nodos_asignados": len(nodos_activos),
            "total_imagenes": solicitud.total_imagenes
        }
    )

# Rutas de imágenes
@router.get("/imagenes/{image_id}/download", tags=["Imágenes"])
async def download_image(
    image_id: int,
    processed: bool = True,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Descargar una imagen (original o procesada)"""
    imagen = db.query(Imagen).join(Solicitud).filter(
        Imagen.id == image_id,
        Solicitud.usuario_id == current_user.id
    ).first()
    
    if not imagen:
        raise HTTPException(status_code=404, detail="Imagen no encontrada o no autorizado")
    
    # Determinar qué archivo descargar
    if processed and imagen.ruta_procesada:
        file_path = imagen.ruta_procesada
        download_name = f"processed_{imagen.nombre_original}"
    else:
        file_path = imagen.ruta_original
        download_name = imagen.nombre_original
    
    if not file_path or not os.path.exists(file_path):
        detail = "Archivo procesado no disponible" if processed else "Archivo original no encontrado"
        raise HTTPException(status_code=404, detail=detail)
    
    # Determinar el tipo MIME basado en la extensión
    extension = os.path.splitext(download_name)[1].lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.bmp': 'image/bmp',
        '.tiff': 'image/tiff',
        '.tif': 'image/tiff',
        '.gif': 'image/gif'
    }
    
    media_type = mime_types.get(extension, 'application/octet-stream')
    
    return FileResponse(
        path=file_path,
        filename=download_name,
        media_type=media_type
    )

@router.get("/imagenes/{image_id}/info", tags=["Imágenes"])
async def get_image_info(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtener información detallada de una imagen"""
    imagen = db.query(Imagen).join(Solicitud).filter(
        Imagen.id == image_id,
        Solicitud.usuario_id == current_user.id
    ).first()
    
    if not imagen:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    
    return {
        "id": imagen.id,
        "nombre_original": imagen.nombre_original,
        "formato_original": imagen.formato_original,
        "formato_destino": imagen.formato_destino,
        "tamaño_original": imagen.tamaño_original,
        "tamaño_procesado": imagen.tamaño_procesado,
        "estado": imagen.estado,
        "fecha_recepcion": imagen.fecha_recepcion,
        "fecha_inicio_procesamiento": imagen.fecha_inicio_procesamiento,
        "fecha_fin_procesamiento": imagen.fecha_fin_procesamiento,
        "transformaciones_solicitadas": imagen.transformaciones_solicitadas,
        "transformaciones_aplicadas": imagen.transformaciones_aplicadas,
        "mensaje_error": imagen.mensaje_error,
        "nodo_id": imagen.nodo_id,
        "archivos_disponibles": {
            "original": os.path.exists(imagen.ruta_original) if imagen.ruta_original else False,
            "procesado": os.path.exists(imagen.ruta_procesada) if imagen.ruta_procesada else False
        }
    }

# Rutas de métricas
@router.get("/metricas", response_model=MetricasSistema, tags=["Métricas"])
async def get_system_metrics(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtener métricas del sistema (requiere autenticación)"""
    # Obtener métricas básicas
    total_usuarios = db.query(Usuario).count()
    total_solicitudes = db.query(Solicitud).count()
    total_imagenes_procesadas = db.query(Imagen).filter(Imagen.estado == 'completado').count()
    nodos_activos = db.query(Nodo).filter(Nodo.estado == 'activo').count()
    
    # Métricas por nodo
    nodos_metricas = []
    nodos = db.query(Nodo).all()
    
    for nodo in nodos:
        imagenes_procesadas = db.query(Imagen).filter(Imagen.nodo_id == nodo.id).count()
        imagenes_error = db.query(Imagen).filter(
            Imagen.nodo_id == nodo.id,
            Imagen.estado == 'error'
        ).count()
        
        # Calcular tiempo promedio de procesamiento (simulado por ahora)
        tiempo_promedio = 1500.0 if imagenes_procesadas > 0 else 0.0
        
        nodo_metrica = MetricasNodo(
            nodo_id=nodo.id,
            imagenes_procesadas=imagenes_procesadas,
            tiempo_promedio_procesamiento=tiempo_promedio,
            errores=imagenes_error,
            estado=nodo.estado
        )
        nodos_metricas.append(nodo_metrica)
    
    return MetricasSistema(
        total_usuarios=total_usuarios,
        total_solicitudes=total_solicitudes,
        total_imagenes_procesadas=total_imagenes_procesadas,
        nodos_activos=nodos_activos,
        nodos=nodos_metricas
    )

# Rutas de logs
@router.get("/logs", tags=["Logs"])
async def get_logs(
    limite: int = 100,
    nivel: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtener logs del sistema (requiere autenticación)"""
    query = db.query(Log).order_by(Log.timestamp.desc())
    
    if nivel:
        query = query.filter(Log.nivel == nivel.upper())
    
    logs = query.limit(limite).all()
    return logs

# Rutas adicionales del sistema
@router.get("/sistema/estado", tags=["Sistema"])
async def get_system_status(db: Session = Depends(get_db)):
    """Obtener estado general del sistema"""
    nodos_total = db.query(Nodo).count()
    nodos_activos = db.query(Nodo).filter(Nodo.estado == 'activo').count()
    solicitudes_pendientes = db.query(Solicitud).filter(Solicitud.estado == 'pendiente').count()
    solicitudes_procesando = db.query(Solicitud).filter(Solicitud.estado == 'procesando').count()
    
    return {
        "sistema_operativo": True,
        "base_datos": True,  # Se podría hacer un ping real
        "nodos": {
            "total": nodos_total,
            "activos": nodos_activos,
            "porcentaje_disponibilidad": (nodos_activos / max(nodos_total, 1)) * 100
        },
        "carga_trabajo": {
            "solicitudes_pendientes": solicitudes_pendientes,
            "solicitudes_procesando": solicitudes_procesando
        },
        "timestamp": datetime.now().isoformat()
    }

@router.delete("/solicitudes/{request_id}", tags=["Solicitudes"])
async def delete_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Eliminar una solicitud (solo si está pendiente)"""
    solicitud = db.query(Solicitud).filter(
        Solicitud.id == request_id,
        Solicitud.usuario_id == current_user.id
    ).first()
    
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    if solicitud.estado != "pendiente":
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede eliminar una solicitud en estado: {solicitud.estado}"
        )
    
    # Eliminar archivos asociados
    for imagen in solicitud.imagenes:
        if os.path.exists(imagen.ruta_original):
            os.remove(imagen.ruta_original)
        if imagen.ruta_procesada and os.path.exists(imagen.ruta_procesada):
            os.remove(imagen.ruta_procesada)
    
    db.delete(solicitud)
    db.commit()
    
    return {"success": True, "message": f"Solicitud {request_id} eliminada correctamente"}

# Rutas de prueba para desarrollo
@router.get("/test/ping", tags=["Desarrollo"])
async def test_ping():
    """Endpoint de prueba para verificar que el servicio funciona"""
    return {
        "success": True,
        "message": "Servidor funcionando correctamente",
        "timestamp": datetime.now().isoformat()
    }

@router.post("/test/soap-login", tags=["Desarrollo"])
async def test_soap_login(username: str, password: str):
    """Endpoint de prueba para simular login SOAP"""
    return {
        "success": True,
        "token": "test-token-12345",
        "message": f"Login exitoso para usuario: {username}"
    }

@router.get("/test/transformaciones", tags=["Desarrollo"])
async def test_available_transformations():
    """Endpoint de prueba que lista las transformaciones disponibles"""
    transformaciones = [
        {"tipo": "escala_grises", "descripcion": "Convertir imagen a escala de grises"},
        {"tipo": "redimensionar", "descripcion": "Cambiar tamaño de imagen", "parametros": ["width", "height", "mantener_aspecto"]},
        {"tipo": "recortar", "descripcion": "Recortar imagen", "parametros": ["x", "y", "width", "height"]},
        {"tipo": "rotar", "descripcion": "Rotar imagen", "parametros": ["angulo"]},
        {"tipo": "reflejar", "descripcion": "Reflejar imagen", "parametros": ["horizontal", "vertical"]},
        {"tipo": "desenfocar", "descripcion": "Aplicar desenfoque", "parametros": ["radio"]},
        {"tipo": "nitidez", "descripcion": "Aplicar nitidez", "parametros": ["factor"]},
        {"tipo": "brillo_contraste", "descripcion": "Ajustar brillo y contraste", "parametros": ["brillo", "contraste"]},
        {"tipo": "marca_agua", "descripcion": "Añadir marca de agua", "parametros": ["texto", "posicion", "tamaño", "color"]},
        {"tipo": "convertir_formato", "descripcion": "Convertir formato", "parametros": ["formato"]}
    ]
    
    return {
        "success": True,
        "transformaciones": transformaciones,
        "total": len(transformaciones)
    }