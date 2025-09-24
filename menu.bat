@echo off
title Sistema Distribuido de Procesamiento de Imagenes

echo ======================================
echo   SISTEMA DISTRIBUIDO DE PROCESAMIENTO
echo            DE IMAGENES v1.0
echo ======================================
echo.
echo Estado del Avance 2: ✅ COMPLETADO
echo.
echo Características implementadas:
echo ✅ Servidor de aplicación Python (FastAPI)
echo ✅ Interfaz Swagger (http://localhost:8000/docs)
echo ✅ Servicios SOAP (/soap?wsdl)
echo ✅ Comunicación gRPC con nodos
echo ✅ Base de datos MySQL con todas las tablas
echo ✅ Autenticación JWT
echo ✅ Procesamiento de imágenes (10 transformaciones)
echo ✅ Nodos de procesamiento con hilos
echo ✅ Sistema de logs y métricas
echo ✅ Mensajes de prueba para todos los métodos
echo.
echo ======================================

:menu
echo.
echo OPCIONES DISPONIBLES:
echo.
echo 1. Configurar sistema (primera vez)
echo 2. Iniciar servidor de aplicación
echo 3. Iniciar nodo de procesamiento
echo 4. Ejecutar pruebas del sistema
echo 5. Crear imágenes de prueba
echo 6. Abrir documentación
echo 7. Ver estado del sistema
echo 8. Salir
echo.

set /p choice="Selecciona una opción (1-8): "

if "%choice%"=="1" goto setup
if "%choice%"=="2" goto server
if "%choice%"=="3" goto node
if "%choice%"=="4" goto tests
if "%choice%"=="5" goto images
if "%choice%"=="6" goto docs
if "%choice%"=="7" goto status
if "%choice%"=="8" goto exit
goto menu

:setup
echo.
echo 🔧 Configurando sistema...
call init.bat
echo.
echo ⚠️ RECORDATORIO: 
echo 1. Instalar MySQL Server
echo 2. Crear base de datos: CREATE DATABASE sistema_imagenes;
echo 3. Ejecutar: database\create_tables.sql
echo.
pause
goto menu

:server
echo.
echo 🖥️ Iniciando servidor de aplicación...
call venv\Scripts\activate.bat
cd servidor_aplicacion
python main.py
cd ..
pause
goto menu

:node
echo.
set /p node_id="ID del nodo (ej: nodo-001): "
set /p port="Puerto gRPC (ej: 50051): "
echo.
echo 🔄 Iniciando nodo %node_id% en puerto %port%...
call venv\Scripts\activate.bat
python nodos\nodo.py --node-id %node_id% --port %port%
pause
goto menu

:tests
echo.
echo 🧪 Ejecutando pruebas...
call run_tests.bat
goto menu

:images
echo.
echo 🖼️ Creando imágenes de prueba...
call venv\Scripts\activate.bat
python tests\create_test_images.py
pause
goto menu

:docs
echo.
echo 📖 Abriendo documentación...
start http://localhost:8000/docs
start http://localhost:8000/soap?wsdl
echo.
echo URLs importantes:
echo - Swagger UI: http://localhost:8000/docs
echo - SOAP WSDL: http://localhost:8000/soap?wsdl
echo - Health Check: http://localhost:8000/health
echo - API Info: http://localhost:8000/info
pause
goto menu

:status
echo.
echo 📊 Estado del sistema:
echo ======================================
call venv\Scripts\activate.bat
python -c "import requests; r=requests.get('http://localhost:8000/health'); print('✅ Servidor:', r.status_code if r.status_code==200 else '❌ Offline')" 2>nul || echo "❌ Servidor: Offline"
echo.
echo Puertos en uso:
netstat -an | findstr :8000 | findstr LISTENING >nul && echo "✅ Puerto 8000: Ocupado (Servidor)" || echo "❌ Puerto 8000: Libre"
netstat -an | findstr :50051 | findstr LISTENING >nul && echo "✅ Puerto 50051: Ocupado (Nodo 1)" || echo "❌ Puerto 50051: Libre"
netstat -an | findstr :50052 | findstr LISTENING >nul && echo "✅ Puerto 50052: Ocupado (Nodo 2)" || echo "❌ Puerto 50052: Libre"
echo.
pause
goto menu

:exit
echo.
echo 👋 ¡Gracias por usar el Sistema de Procesamiento de Imágenes!
echo.
echo Para soporte, consulta:
echo - README.md (documentación completa)
echo - Logs en directorio logs/
echo - Health check: /health
echo.
timeout /t 3 >nul
exit