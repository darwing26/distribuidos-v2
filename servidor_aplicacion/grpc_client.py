# Cliente gRPC para comunicación con nodos
import grpc
import logging
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import asyncio
from servidor_aplicacion.config import Config

# Importar los módulos generados de protobuf (se generarán después)
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from proto import image_processing_pb2
    from proto import image_processing_pb2_grpc
except ImportError:
    # Para desarrollo, crear clases mock
    class MockImageProcessing:
        class TransformationType:
            GRAYSCALE = 1
            RESIZE = 2
            CROP = 3
            ROTATE = 4
            FLIP = 5
            BLUR = 6
            SHARPEN = 7
            BRIGHTNESS_CONTRAST = 8
            WATERMARK = 9
            CONVERT_FORMAT = 10
            
        class NodeState:
            ACTIVE = 1
            INACTIVE = 2
            ERROR = 3
            BUSY = 4
    
    image_processing_pb2 = MockImageProcessing()
    image_processing_pb2_grpc = None

logger = logging.getLogger(__name__)

class GRPCClient:
    def __init__(self):
        self.timeout = Config.NODO_TIMEOUT
        self.channels = {}  # Cache de canales gRPC
        
    def get_channel(self, host: str, port: int):
        """Obtener o crear un canal gRPC para un nodo"""
        key = f"{host}:{port}"
        if key not in self.channels:
            address = f"{host}:{port}"
            self.channels[key] = grpc.insecure_channel(address)
        return self.channels[key]
    
    def close_channels(self):
        """Cerrar todos los canales gRPC"""
        for channel in self.channels.values():
            channel.close()
        self.channels.clear()
    
    def ping_node(self, host: str, port: int) -> Tuple[bool, str]:
        """Hacer ping a un nodo para verificar conectividad"""
        try:
            channel = self.get_channel(host, port)
            if image_processing_pb2_grpc is None:
                # Mock response para desarrollo
                return True, f"Nodo {host}:{port} disponible (mock)"
            
            stub = image_processing_pb2_grpc.ImageProcessingServiceStub(channel)
            request = image_processing_pb2.PingRequest(timestamp=str(int(time.time())))
            
            response = stub.Ping(request, timeout=self.timeout)
            return True, f"Nodo {response.node_id} responde correctamente"
            
        except grpc.RpcError as e:
            logger.error(f"Error de gRPC al hacer ping a {host}:{port}: {e}")
            return False, f"Error de conexión: {e.code()}"
        except Exception as e:
            logger.error(f"Error inesperado al hacer ping a {host}:{port}: {e}")
            return False, f"Error inesperado: {str(e)}"
    
    def get_node_status(self, host: str, port: int, node_id: str) -> Dict:
        """Obtener el estado de un nodo"""
        try:
            channel = self.get_channel(host, port)
            if image_processing_pb2_grpc is None:
                # Mock response para desarrollo
                return {
                    'node_id': node_id,
                    'state': 'ACTIVE',
                    'active_jobs': 0,
                    'completed_jobs': 10,
                    'failed_jobs': 0,
                    'cpu_usage': 25.5,
                    'memory_usage': 45.2
                }
            
            stub = image_processing_pb2_grpc.ImageProcessingServiceStub(channel)
            request = image_processing_pb2.NodeStatusRequest(node_id=node_id)
            
            response = stub.GetNodeStatus(request, timeout=self.timeout)
            
            return {
                'node_id': response.node_id,
                'state': response.state,
                'active_jobs': response.active_jobs,
                'completed_jobs': response.completed_jobs,
                'failed_jobs': response.failed_jobs,
                'cpu_usage': response.cpu_usage,
                'memory_usage': response.memory_usage
            }
            
        except grpc.RpcError as e:
            logger.error(f"Error al obtener estado del nodo {node_id}: {e}")
            raise Exception(f"No se pudo obtener el estado del nodo: {e}")
        except Exception as e:
            logger.error(f"Error inesperado al obtener estado del nodo {node_id}: {e}")
            raise
    
    def process_image(
        self, 
        host: str, 
        port: int, 
        image_id: str,
        image_path: str, 
        output_path: str,
        transformations: List[Dict]
    ) -> Dict:
        """Enviar una imagen a procesar a un nodo"""
        try:
            channel = self.get_channel(host, port)
            if image_processing_pb2_grpc is None:
                # Mock response para desarrollo
                return {
                    'success': True,
                    'message': f'Imagen {image_id} procesada correctamente (mock)',
                    'processed_image_path': output_path,
                    'stats': {
                        'processing_time_ms': 1500,
                        'file_size_before': 2048576,
                        'file_size_after': 1536789,
                        'format_before': 'PNG',
                        'format_after': 'JPG'
                    },
                    'errors': []
                }
            
            stub = image_processing_pb2_grpc.ImageProcessingServiceStub(channel)
            
            # Convertir transformaciones al formato protobuf
            proto_transformations = []
            for trans in transformations:
                transformation_type = getattr(
                    image_processing_pb2.TransformationType, 
                    trans['tipo'].upper(), 
                    image_processing_pb2.TransformationType.UNKNOWN
                )
                
                proto_trans = image_processing_pb2.Transformation(
                    type=transformation_type,
                    parameters=trans.get('parametros', {})
                )
                proto_transformations.append(proto_trans)
            
            request = image_processing_pb2.ProcessImageRequest(
                image_id=image_id,
                image_path=image_path,
                output_path=output_path,
                transformations=proto_transformations
            )
            
            response = stub.ProcessImage(request, timeout=self.timeout * 2)  # Más tiempo para procesamiento
            
            return {
                'success': response.success,
                'message': response.message,
                'processed_image_path': response.processed_image_path,
                'stats': {
                    'processing_time_ms': response.stats.processing_time_ms,
                    'file_size_before': response.stats.file_size_before,
                    'file_size_after': response.stats.file_size_after,
                    'format_before': response.stats.format_before,
                    'format_after': response.stats.format_after
                },
                'errors': list(response.errors)
            }
            
        except grpc.RpcError as e:
            logger.error(f"Error al procesar imagen {image_id} en nodo {host}:{port}: {e}")
            raise Exception(f"Error de procesamiento: {e}")
        except Exception as e:
            logger.error(f"Error inesperado al procesar imagen {image_id}: {e}")
            raise

    def process_images_parallel(
        self, 
        nodos_disponibles: List[Dict],
        imagenes: List[Dict]
    ) -> List[Dict]:
        """Procesar múltiples imágenes en paralelo usando varios nodos"""
        results = []
        
        with ThreadPoolExecutor(max_workers=min(len(nodos_disponibles), len(imagenes))) as executor:
            # Distribuir imágenes entre nodos disponibles
            future_to_image = {}
            
            for i, imagen in enumerate(imagenes):
                # Seleccionar nodo (round-robin)
                nodo = nodos_disponibles[i % len(nodos_disponibles)]
                
                future = executor.submit(
                    self.process_image,
                    nodo['direccion_ip'],
                    nodo['puerto'],
                    str(imagen['id']),
                    imagen['ruta_original'],
                    imagen['ruta_procesada'],
                    imagen['transformaciones_solicitadas']
                )
                future_to_image[future] = {
                    'imagen': imagen,
                    'nodo': nodo
                }
            
            # Recoger resultados
            for future in as_completed(future_to_image):
                image_info = future_to_image[future]
                try:
                    result = future.result()
                    result['imagen_id'] = image_info['imagen']['id']
                    result['nodo_id'] = image_info['nodo']['id']
                    results.append(result)
                    
                    logger.info(f"Imagen {image_info['imagen']['id']} procesada exitosamente en nodo {image_info['nodo']['identificador']}")
                    
                except Exception as e:
                    logger.error(f"Error al procesar imagen {image_info['imagen']['id']}: {e}")
                    results.append({
                        'imagen_id': image_info['imagen']['id'],
                        'nodo_id': image_info['nodo']['id'],
                        'success': False,
                        'message': str(e),
                        'errors': [str(e)]
                    })
        
        return results

# Instancia global del cliente
grpc_client = GRPCClient()