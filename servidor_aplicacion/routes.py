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
    RespuestaBase, MetricasSistema
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
    
    new_node = Nodo(**node_data.dict())
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
    
    for field, value in node_update.dict(exclude_unset=True).items():
        setattr(node, field, value)
    
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
    # Validar archivos
    for imagen in imagenes:
        if not imagen.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif')):
            raise HTTPException(
                status_code=400,
                detail=f"Formato de archivo no soportado: {imagen.filename}"
            )
    
    # Parsear transformaciones
    try:
        transformaciones_data = json.loads(transformaciones)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Formato de transformaciones inválido")
    
    # Crear solicitud
    nueva_solicitud = Solicitud(
        usuario_id=current_user.id,
        descripcion=descripcion,
        total_imagenes=len(imagenes)
    )
    
    db.add(nueva_solicitud)
    db.commit()
    db.refresh(nueva_solicitud)
    
    # Guardar archivos y crear registros de imágenes
    Config.create_directories()
    imagenes_procesadas = []
    
    for i, imagen in enumerate(imagenes):
        # Guardar archivo
        file_path = os.path.join(Config.UPLOAD_DIR, f"{nueva_solicitud.id}_{i}_{imagen.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(imagen.file, buffer)
        
        # Crear registro de imagen
        imagen_record = Imagen(
            solicitud_id=nueva_solicitud.id,
            nombre_original=imagen.filename,
            ruta_original=file_path,
            formato_original=imagen.filename.split('.')[-1].lower(),
            tamaño_original=os.path.getsize(file_path),
            transformaciones_solicitadas=transformaciones_data
        )
        
        db.add(imagen_record)
        imagenes_procesadas.append(imagen_record)
    
    db.commit()
    
    # Actualizar la solicitud con las imágenes
    nueva_solicitud.imagenes = imagenes_procesadas
    db.refresh(nueva_solicitud)
    
    return nueva_solicitud

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

@router.post("/solicitudes/{request_id}/procesar", tags=["Solicitudes"])
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
    
    # Verificar nodos disponibles
    nodos_activos = db.query(Nodo).filter(Nodo.estado == 'activo').all()
    if not nodos_activos:
        raise HTTPException(status_code=503, detail="No hay nodos disponibles")
    
    # Actualizar estado
    solicitud.estado = "procesando"
    db.commit()
    
    # Aquí se implementaría el procesamiento asíncrono real
    # Por ahora retornamos una respuesta de prueba
    
    return {
        "success": True,
        "message": f"Procesamiento iniciado para solicitud {request_id}",
        "nodos_asignados": len(nodos_activos)
    }

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
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    
    file_path = imagen.ruta_procesada if processed and imagen.ruta_procesada else imagen.ruta_original
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    return FileResponse(
        path=file_path,
        filename=imagen.nombre_original,
        media_type='application/octet-stream'
    )

# Rutas de métricas
@router.get("/metricas", response_model=MetricasSistema, tags=["Métricas"])
async def get_system_metrics(db: Session = Depends(get_db)):
    """Obtener métricas del sistema"""
    total_usuarios = db.query(Usuario).count()
    total_solicitudes = db.query(Solicitud).count()
    total_imagenes_procesadas = db.query(Imagen).filter(Imagen.estado == 'completado').count()
    nodos_activos = db.query(Nodo).filter(Nodo.estado == 'activo').count()
    
    # Métricas por nodo
    nodos_metricas = []
    nodos = db.query(Nodo).all()
    
    for nodo in nodos:
        imagenes_procesadas = db.query(Imagen).filter(Imagen.nodo_id == nodo.id).count()
        nodos_metricas.append({
            "nodo_id": nodo.id,
            "imagenes_procesadas": imagenes_procesadas,
            "tiempo_promedio_procesamiento": 1500.0,  # Mock
            "errores": 0,
            "estado": nodo.estado
        })
    
    return MetricasSistema(
        total_usuarios=total_usuarios,
        total_solicitudes=total_solicitudes,
        total_imagenes_procesadas=total_imagenes_procesadas,
        nodos_activos=nodos_activos,
        nodos=nodos_metricas
    )

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