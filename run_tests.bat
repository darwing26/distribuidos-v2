@echo off
echo ======================================
echo PRUEBAS DEL SISTEMA DISTRIBUIDO
echo ======================================

REM Activar entorno virtual
call venv\Scripts\activate.bat

echo.
echo 🖼️ Creando imágenes de prueba...
python tests\create_test_images.py

echo.
echo 🧪 Ejecutando pruebas del sistema...
echo (Asegurate de que el servidor esté corriendo en otra terminal)
python tests\test_sistema.py

echo.
echo ======================================
echo Pruebas completadas
echo ======================================
echo.
echo 💡 Para ver la interfaz Swagger:
echo    http://localhost:8000/docs
echo.
echo 💡 Para ver el WSDL de SOAP:
echo    http://localhost:8000/soap?wsdl
echo.

pause