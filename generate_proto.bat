@echo off
echo Generando archivos protobuf...

REM Activar el entorno virtual
call venv\Scripts\activate.bat

REM Crear directorio proto si no existe
mkdir proto 2>nul

REM Generar archivos Python desde los .proto
python -m grpc_tools.protoc ^
    --proto_path=proto ^
    --python_out=proto ^
    --grpc_python_out=proto ^
    proto\image_processing.proto

REM Crear archivos __init__.py para que sea un paquete Python
echo # Paquete protobuf generado > proto\__init__.py

echo.
echo Archivos protobuf generados exitosamente!
echo Los siguientes archivos fueron creados:
echo - proto\image_processing_pb2.py
echo - proto\image_processing_pb2_grpc.py
echo.

pause