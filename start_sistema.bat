@echo off
echo ======================================
echo INICIANDO SISTEMA DISTRIBUIDO DE PROCESAMIENTO DE IMAGENES
echo ======================================

REM Verificar que el entorno virtual esté activado
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Entorno virtual no encontrado. Ejecuta init.bat primero.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo.
echo 🔧 Verificando configuracion...

REM Verificar que MySQL esté corriendo (opcional)
echo 📊 Nota: Asegurate de que MySQL este corriendo y la base de datos creada.
echo    Ejecuta el script: database\create_tables.sql

echo.
echo 🚀 Iniciando componentes del sistema...

REM Crear directorios si no existen
mkdir uploads 2>nul
mkdir processed_images 2>nul
mkdir logs 2>nul
mkdir work 2>nul
mkdir work\input 2>nul
mkdir work\output 2>nul
mkdir work\temp 2>nul
mkdir work\logs 2>nul

echo.
echo 📋 INSTRUCCIONES DE USO:
echo ======================================
echo.
echo 1. SERVIDOR DE APLICACION:
echo    cd servidor_aplicacion
echo    python main.py
echo.
echo 2. NODOS DE PROCESAMIENTO (en terminales separados):
echo    python nodos\nodo.py --node-id nodo-001 --port 50051
echo    python nodos\nodo.py --node-id nodo-002 --port 50052
echo    python nodos\nodo.py --node-id nodo-003 --port 50053
echo.
echo 3. ACCEDER AL SISTEMA:
echo    - Swagger UI: http://localhost:8000/docs
echo    - API REST: http://localhost:8000/api/v1
echo    - SOAP WSDL: http://localhost:8000/soap?wsdl
echo    - Health Check: http://localhost:8000/health
echo.
echo 4. PROBAR EL SISTEMA:
echo    python tests\test_sistema.py
echo.
echo ======================================

echo.
set /p choice="¿Quieres iniciar el servidor de aplicacion ahora? (s/n): "
if /i "%choice%"=="s" (
    echo.
    echo 🖥️ Iniciando servidor de aplicacion...
    cd servidor_aplicacion
    python main.py
) else (
    echo.
    echo ℹ️ Para iniciar manualmente:
    echo    cd servidor_aplicacion
    echo    python main.py
    echo.
)

pause