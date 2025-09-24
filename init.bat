@echo off
echo ======================================
echo Inicializando Sistema Distribuido de Procesamiento de Imagenes
echo ======================================

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado. Instala Python 3.8+ desde python.org
    pause
    exit /b 1
)

REM Crear el entorno virtual de Python
echo Creando entorno virtual...
python -m venv venv
if errorlevel 1 (
    echo ❌ Error creando entorno virtual
    pause
    exit /b 1
)

REM Activar el entorno virtual
echo Activando entorno virtual...
call venv\Scripts\activate.bat

REM Instalar dependencias
echo Instalando dependencias...
pip install -r requirements.txt

REM Crear directorios necesarios
echo Creando directorios...
mkdir uploads
mkdir processed_images
mkdir logs
mkdir database

echo ======================================
echo Configuracion completada!
echo ======================================
echo.
echo Para usar el sistema:
echo 1. Activar el entorno: venv\Scripts\activate.bat
echo 2. Iniciar la base de datos MySQL
echo 3. Ejecutar el script SQL: database\create_tables.sql
echo 4. Iniciar el servidor: python servidor_aplicacion\main.py
echo 5. Iniciar nodos: python nodos\nodo.py
echo 6. Abrir la aplicacion web en: http://localhost:8000/docs (Swagger)
echo ======================================

pause