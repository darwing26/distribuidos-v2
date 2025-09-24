# Scripts de prueba para el sistema

## Test del servidor de aplicación
import asyncio
import httpx
import json

async def test_servidor_aplicacion():
    """Probar las rutas principales del servidor de aplicación"""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        print("🧪 Probando servidor de aplicación...")
        
        # Test 1: Health check
        try:
            response = await client.get(f"{base_url}/health")
            print(f"✅ Health check: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"❌ Health check falló: {e}")
        
        # Test 2: Información del servidor
        try:
            response = await client.get(f"{base_url}/info")
            print(f"✅ Server info: {response.status_code}")
        except Exception as e:
            print(f"❌ Server info falló: {e}")
        
        # Test 3: Swagger docs
        try:
            response = await client.get(f"{base_url}/docs")
            print(f"✅ Swagger docs: {response.status_code}")
        except Exception as e:
            print(f"❌ Swagger docs falló: {e}")
        
        # Test 4: SOAP WSDL
        try:
            response = await client.get(f"{base_url}/soap?wsdl")
            print(f"✅ SOAP WSDL: {response.status_code}")
        except Exception as e:
            print(f"❌ SOAP WSDL falló: {e}")

async def test_api_endpoints():
    """Probar endpoints específicos de la API"""
    base_url = "http://localhost:8000/api/v1"
    
    async with httpx.AsyncClient() as client:
        print("\n🧪 Probando endpoints de la API...")
        
        # Test 1: Obtener transformaciones disponibles
        try:
            response = await client.get(f"{base_url}/transformaciones")
            print(f"✅ Transformaciones: {response.status_code}")
            if response.status_code == 200:
                transformaciones = response.json()
                print(f"   📋 {len(transformaciones)} transformaciones disponibles")
        except Exception as e:
            print(f"❌ Transformaciones falló: {e}")
        
        # Test 2: Obtener nodos
        try:
            response = await client.get(f"{base_url}/nodos")
            print(f"✅ Nodos: {response.status_code}")
            if response.status_code == 200:
                nodos = response.json()
                print(f"   🖥️ {len(nodos)} nodos registrados")
        except Exception as e:
            print(f"❌ Nodos falló: {e}")
        
        # Test 3: Métricas del sistema
        try:
            response = await client.get(f"{base_url}/metricas")
            print(f"✅ Métricas: {response.status_code}")
        except Exception as e:
            print(f"❌ Métricas falló: {e}")
        
        # Test 4: Ping de prueba
        try:
            response = await client.get(f"{base_url}/test/ping")
            print(f"✅ Test ping: {response.status_code}")
        except Exception as e:
            print(f"❌ Test ping falló: {e}")

async def test_autenticacion():
    """Probar sistema de autenticación"""
    base_url = "http://localhost:8000/api/v1"
    
    async with httpx.AsyncClient() as client:
        print("\n🧪 Probando autenticación...")
        
        # Test 1: Registro de usuario (si no existe)
        user_data = {
            "username": "testuser_" + str(int(asyncio.get_event_loop().time())),
            "email": f"test_{int(asyncio.get_event_loop().time())}@test.com",
            "password": "password123"
        }
        
        try:
            response = await client.post(f"{base_url}/auth/register", json=user_data)
            print(f"✅ Registro: {response.status_code}")
        except Exception as e:
            print(f"❌ Registro falló: {e}")
        
        # Test 2: Login
        try:
            login_data = {
                "username": user_data["username"],
                "password": user_data["password"]
            }
            response = await client.post(f"{base_url}/auth/login", json=login_data)
            print(f"✅ Login: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                token = token_data.get("access_token")
                
                # Test 3: Obtener info del usuario con token
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get(f"{base_url}/auth/me", headers=headers)
                print(f"✅ Usuario autenticado: {response.status_code}")
        
        except Exception as e:
            print(f"❌ Login falló: {e}")

def test_soap_client():
    """Probar cliente SOAP básico"""
    print("\n🧪 Probando cliente SOAP...")
    
    try:
        from zeep import Client
        
        # Crear cliente SOAP
        wsdl_url = "http://localhost:8000/soap?wsdl"
        client = Client(wsdl_url)
        
        print(f"✅ Cliente SOAP creado")
        print("📋 Operaciones disponibles:")
        
        # Listar operaciones disponibles
        for service_name, service in client.wsdl.services.items():
            for port_name, port in service.ports.items():
                for operation in port.binding._operations.values():
                    print(f"   - {operation.name}")
        
        # Test básico de login
        try:
            result = client.service.login("admin", "admin123")
            print(f"✅ SOAP Login test: {result}")
        except Exception as e:
            print(f"⚠️ SOAP Login: {e} (normal si no hay datos de prueba)")
    
    except ImportError:
        print("❌ zeep no disponible, instalar con: pip install zeep")
    except Exception as e:
        print(f"❌ SOAP client falló: {e}")

def test_grpc_client():
    """Probar cliente gRPC básico"""
    print("\n🧪 Probando cliente gRPC...")
    
    try:
        import grpc
        from servidor_aplicacion.grpc_client import grpc_client
        
        # Test ping a nodos de ejemplo
        test_nodes = [
            {"host": "127.0.0.1", "port": 50051},
            {"host": "127.0.0.1", "port": 50052},
            {"host": "127.0.0.1", "port": 50053},
        ]
        
        for node in test_nodes:
            success, message = grpc_client.ping_node(node["host"], node["port"])
            status = "✅" if success else "❌"
            print(f"{status} Nodo {node['host']}:{node['port']}: {message}")
    
    except ImportError:
        print("❌ grpc no disponible, instalar con: pip install grpcio")
    except Exception as e:
        print(f"⚠️ gRPC client: {e} (normal si no hay nodos activos)")

async def run_all_tests():
    """Ejecutar todas las pruebas"""
    print("🚀 Iniciando pruebas del sistema...")
    print("=" * 50)
    
    await test_servidor_aplicacion()
    await test_api_endpoints()
    await test_autenticacion()
    test_soap_client()
    test_grpc_client()
    
    print("\n" + "=" * 50)
    print("✅ Pruebas completadas")
    print("\n💡 Para usar el sistema:")
    print("   1. Abrir http://localhost:8000/docs para Swagger UI")
    print("   2. Abrir http://localhost:8000/soap?wsdl para SOAP WSDL")
    print("   3. Verificar nodos en http://localhost:8000/api/v1/nodos")

if __name__ == "__main__":
    asyncio.run(run_all_tests())