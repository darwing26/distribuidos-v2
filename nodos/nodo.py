# Nodo principal - Punto de entrada
from grpc_server import NodoServer
from config import NodoConfig
import sys
import argparse
import signal
import logging

def signal_handler(signum, frame):
    """Manejador de señales para cierre graceful"""
    logger.info(f"Señal {signum} recibida, cerrando nodo...")
    sys.exit(0)

def main():
    """Función principal del nodo"""
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Nodo de procesamiento de imágenes')
    parser.add_argument('--node-id', default=NodoConfig.NODE_ID, 
                       help='Identificador único del nodo')
    parser.add_argument('--port', type=int, default=NodoConfig.GRPC_PORT,
                       help='Puerto gRPC para el servidor')
    parser.add_argument('--host', default=NodoConfig.GRPC_HOST,
                       help='Host para el servidor gRPC')
    parser.add_argument('--max-jobs', type=int, default=NodoConfig.MAX_CONCURRENT_JOBS,
                       help='Máximo número de trabajos concurrentes')
    parser.add_argument('--log-level', default=NodoConfig.LOG_LEVEL,
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='Nivel de logging')
    
    args = parser.parse_args()
    
    # Actualizar configuración con argumentos
    NodoConfig.NODE_ID = args.node_id
    NodoConfig.GRPC_PORT = args.port
    NodoConfig.GRPC_HOST = args.host
    NodoConfig.MAX_CONCURRENT_JOBS = args.max_jobs
    NodoConfig.LOG_LEVEL = args.log_level
    
    # Configurar logging
    logger = NodoConfig.setup_logging()
    
    # Configurar manejadores de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Mostrar información de inicio
    logger.info("=" * 50)
    logger.info("NODO DE PROCESAMIENTO DE IMÁGENES")
    logger.info("=" * 50)
    logger.info(f"ID del nodo: {args.node_id}")
    logger.info(f"Puerto gRPC: {args.port}")
    logger.info(f"Host: {args.host}")
    logger.info(f"Máx. trabajos concurrentes: {args.max_jobs}")
    logger.info(f"Nivel de log: {args.log_level}")
    logger.info(f"Directorio de trabajo: {NodoConfig.WORK_DIR}")
    logger.info("=" * 50)
    
    try:
        # Crear y iniciar servidor
        server = NodoServer(node_id=args.node_id, port=args.port)
        server.start()
    
    except Exception as e:
        logger.error(f"Error fatal en el nodo: {e}")
        sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Nodo detenido por el usuario")
        sys.exit(0)

if __name__ == "__main__":
    main()