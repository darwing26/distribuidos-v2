# Servidor gRPC del nodo de procesamiento
import grpc
from concurrent import futures
import threading
import time
import psutil
import os
import logging
from typing import Dict, Any

# Importar protobuf generados (mock para desarrollo)
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from proto import image_processing_pb2
    from proto import image_processing_pb2_grpc
except ImportError:
    image_processing_pb2 = None
    image_processing_pb2_grpc = None

class MockGRPC:
    class ProcessImageRequest:
        def __init__(self):
            self.image_id = ""
            self.image_path = ""
            self.output_path = ""
            self.transformations = []
    
    class ProcessImageResponse:
        def __init__(self, success=False, message="", processed_image_path="", stats=None, errors=None):
            self.success = success
            self.message = message
            self.processed_image_path = processed_image_path
            self.stats = stats or MockGRPC.ProcessingStats()
            self.errors = errors or []
    
    class NodeStatusRequest:
        def __init__(self):
            self.node_id = ""
    
    class NodeStatusResponse:
        def __init__(self):
            self.node_id = ""
            self.state = 1  # ACTIVE
            self.active_jobs = 0
            self.completed_jobs = 0
            self.failed_jobs = 0
            self.cpu_usage = 0.0
            self.memory_usage = 0.0
    
    class PingRequest:
        def __init__(self):
            self.timestamp = ""
    
    class PingResponse:
        def __init__(self):
            self.timestamp = ""
            self.node_id = ""
            self.healthy = True
    
    class ProcessingStats:
        def __init__(self):
            self.processing_time_ms = 0
            self.file_size_before = 0
            self.file_size_after = 0
            self.format_before = ""
            self.format_after = ""

# Usar mock para desarrollo si no se cargaron los protobuf reales
if image_processing_pb2 is None:
    image_processing_pb2 = MockGRPC()

from config import NodoConfig
from image_processor import ImageProcessor

logger = logging.getLogger(__name__)

class ImageProcessingServicer:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.processor = ImageProcessor()
        self.active_jobs = 0
        self.completed_jobs = 0
        self.failed_jobs = 0
        self.start_time = time.time()
        self.job_lock = threading.Lock()
    
    def ProcessImage(self, request, context):
        """Procesar una imagen"""
        start_time = time.time()
        
        with self.job_lock:
            self.active_jobs += 1
        
        try:
            logger.info(f"Procesando imagen: {request.image_id}")
            
            # Convertir transformaciones del request
            transformations = []
            if hasattr(request, 'transformations'):
                for trans in request.transformations:
                    trans_dict = {
                        'tipo': self._get_transformation_name(trans.type),
                        'parametros': dict(trans.parameters) if hasattr(trans, 'parameters') else {}
                    }
                    transformations.append(trans_dict)
            
            # Procesar imagen
            result = self.processor.process_image(
                request.image_path,
                request.output_path,
                transformations
            )
            
            # Actualizar contadores
            with self.job_lock:
                self.active_jobs -= 1
                if result['success']:
                    self.completed_jobs += 1
                else:
                    self.failed_jobs += 1
            
            # Crear respuesta
            if image_processing_pb2_grpc is None:
                # Respuesta mock para desarrollo
                return image_processing_pb2.ProcessImageResponse(
                    success=result['success'],
                    message=result['message'],
                    processed_image_path=result.get('processed_image_path', ''),
                    stats=image_processing_pb2.ProcessingStats(),
                    errors=result.get('errors', [])
                )
            else:
                # Respuesta real con protobuf
                stats = image_processing_pb2.ProcessingStats(
                    processing_time_ms=result['stats']['processing_time_ms'],
                    file_size_before=result['stats']['file_size_before'],
                    file_size_after=result['stats']['file_size_after'],
                    format_before=result['stats']['format_before'],
                    format_after=result['stats']['format_after']
                )
                
                return image_processing_pb2.ProcessImageResponse(
                    success=result['success'],
                    message=result['message'],
                    processed_image_path=result.get('processed_image_path', ''),
                    stats=stats,
                    errors=result.get('errors', [])
                )
        
        except Exception as e:
            logger.error(f"Error procesando imagen {request.image_id}: {e}")
            
            with self.job_lock:
                self.active_jobs -= 1
                self.failed_jobs += 1
            
            if image_processing_pb2_grpc is None:
                return image_processing_pb2.ProcessImageResponse(
                    success=False,
                    message=f"Error interno: {str(e)}",
                    errors=[str(e)]
                )
            else:
                return image_processing_pb2.ProcessImageResponse(
                    success=False,
                    message=f"Error interno: {str(e)}",
                    processed_image_path="",
                    stats=image_processing_pb2.ProcessingStats(),
                    errors=[str(e)]
                )
    
    def GetNodeStatus(self, request, context):
        """Obtener estado del nodo"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.virtual_memory()
            
            if image_processing_pb2_grpc is None:
                response = image_processing_pb2.NodeStatusResponse()
                response.node_id = self.node_id
                response.state = 1  # ACTIVE
                response.active_jobs = self.active_jobs
                response.completed_jobs = self.completed_jobs
                response.failed_jobs = self.failed_jobs
                response.cpu_usage = cpu_percent
                response.memory_usage = memory_info.percent
                return response
            else:
                return image_processing_pb2.NodeStatusResponse(
                    node_id=self.node_id,
                    state=image_processing_pb2.NodeState.ACTIVE,
                    active_jobs=self.active_jobs,
                    completed_jobs=self.completed_jobs,
                    failed_jobs=self.failed_jobs,
                    cpu_usage=cpu_percent,
                    memory_usage=memory_info.percent
                )
        
        except Exception as e:
            logger.error(f"Error obteniendo estado del nodo: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return image_processing_pb2.NodeStatusResponse()
    
    def Ping(self, request, context):
        """Responder a ping"""
        try:
            if image_processing_pb2_grpc is None:
                response = image_processing_pb2.PingResponse()
                response.timestamp = str(int(time.time()))
                response.node_id = self.node_id
                response.healthy = True
                return response
            else:
                return image_processing_pb2.PingResponse(
                    timestamp=str(int(time.time())),
                    node_id=self.node_id,
                    healthy=True
                )
        
        except Exception as e:
            logger.error(f"Error en ping: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return image_processing_pb2.PingResponse()
    
    def _get_transformation_name(self, trans_type):
        """Convertir tipo de transformación de protobuf a string"""
        # Mock mapping para desarrollo
        type_map = {
            1: "escala_grises",
            2: "redimensionar",
            3: "recortar",
            4: "rotar",
            5: "reflejar",
            6: "desenfocar",
            7: "nitidez",
            8: "brillo_contraste",
            9: "marca_agua",
            10: "convertir_formato"
        }
        return type_map.get(trans_type, "desconocido")

class NodoServer:
    def __init__(self, node_id: str = None, port: int = None):
        self.node_id = node_id or NodoConfig.NODE_ID
        self.port = port or NodoConfig.GRPC_PORT
        self.server = None
        self.servicer = ImageProcessingServicer(self.node_id)
        
        # Configurar logging
        self.logger = NodoConfig.setup_logging()
        
        # Crear directorios necesarios
        NodoConfig.create_directories()
    
    def start(self):
        """Iniciar el servidor gRPC"""
        try:
            self.server = grpc.server(
                futures.ThreadPoolExecutor(max_workers=NodoConfig.MAX_CONCURRENT_JOBS)
            )
            
            # Registrar servicios
            if image_processing_pb2_grpc is not None:
                image_processing_pb2_grpc.add_ImageProcessingServiceServicer_to_server(
                    self.servicer, self.server
                )
            
            # Configurar puerto
            listen_addr = f'{NodoConfig.GRPC_HOST}:{self.port}'
            self.server.add_insecure_port(listen_addr)
            
            # Iniciar servidor
            self.server.start()
            
            self.logger.info(f"Nodo {self.node_id} iniciado en {listen_addr}")
            self.logger.info(f"Directorio de trabajo: {NodoConfig.WORK_DIR}")
            self.logger.info(f"Máximo trabajos concurrentes: {NodoConfig.MAX_CONCURRENT_JOBS}")
            
            # Mantener el servidor corriendo
            try:
                while True:
                    time.sleep(3600)  # Dormir por 1 hora
            except KeyboardInterrupt:
                self.logger.info("Interrupción recibida, cerrando servidor...")
                self.stop()
        
        except Exception as e:
            self.logger.error(f"Error al iniciar el servidor: {e}")
            raise
    
    def stop(self):
        """Detener el servidor gRPC"""
        if self.server:
            self.logger.info("Deteniendo servidor...")
            self.server.stop(grace=30)  # 30 segundos de gracia
            self.logger.info("Servidor detenido")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado actual del nodo"""
        return {
            'node_id': self.node_id,
            'port': self.port,
            'active_jobs': self.servicer.active_jobs,
            'completed_jobs': self.servicer.completed_jobs,
            'failed_jobs': self.servicer.failed_jobs,
            'uptime': time.time() - self.servicer.start_time,
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'status': 'running' if self.server else 'stopped'
        }

if __name__ == "__main__":
    import sys
    
    # Permitir especificar ID y puerto desde argumentos
    node_id = sys.argv[1] if len(sys.argv) > 1 else None
    port = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    # Crear e iniciar servidor
    server = NodoServer(node_id=node_id, port=port)
    
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()