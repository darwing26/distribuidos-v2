# Simulador de imágenes de prueba
from PIL import Image, ImageDraw, ImageFont
import os
import random

def create_test_images():
    """Crear imágenes de prueba para el sistema"""
    
    # Crear directorio de uploads si no existe
    upload_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    images_created = []
    
    # Colores de prueba
    colors = [
        (255, 0, 0),    # Rojo
        (0, 255, 0),    # Verde
        (0, 0, 255),    # Azul
        (255, 255, 0),  # Amarillo
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Cian
    ]
    
    for i in range(6):
        # Crear imagen de prueba
        width, height = 800, 600
        image = Image.new('RGB', (width, height), colors[i])
        draw = ImageDraw.Draw(image)
        
        # Dibujar texto
        try:
            font = ImageFont.truetype("arial.ttf", 48)
        except:
            font = ImageFont.load_default()
        
        text = f"Imagen de Prueba #{i+1}"
        # Calcular posición centrada del texto
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Dibujar texto con borde
        draw.text((x-2, y-2), text, font=font, fill=(0, 0, 0))  # Borde negro
        draw.text((x, y), text, font=font, fill=(255, 255, 255))  # Texto blanco
        
        # Dibujar algunos elementos gráficos
        # Rectángulo
        draw.rectangle([50, 50, 150, 150], outline=(255, 255, 255), width=3)
        
        # Círculo
        draw.ellipse([width-150, 50, width-50, 150], outline=(255, 255, 255), width=3)
        
        # Líneas
        for j in range(5):
            y_pos = height - 100 + j * 15
            draw.line([50, y_pos, width-50, y_pos], fill=(255, 255, 255), width=2)
        
        # Guardar imagen
        filename = f"test_image_{i+1}.png"
        filepath = os.path.join(upload_dir, filename)
        image.save(filepath, "PNG")
        
        images_created.append({
            'filename': filename,
            'filepath': filepath,
            'size': os.path.getsize(filepath),
            'dimensions': f"{width}x{height}",
            'color': f"RGB{colors[i]}"
        })
        
        print(f"✅ Creada: {filename} ({os.path.getsize(filepath)} bytes)")
    
    # Crear imagen más pequeña para pruebas rápidas
    small_image = Image.new('RGB', (200, 150), (128, 128, 128))
    draw = ImageDraw.Draw(small_image)
    draw.text((50, 60), "Mini", fill=(255, 255, 255))
    
    small_filename = "small_test.jpg"
    small_filepath = os.path.join(upload_dir, small_filename)
    small_image.save(small_filepath, "JPEG", quality=95)
    
    images_created.append({
        'filename': small_filename,
        'filepath': small_filepath,
        'size': os.path.getsize(small_filepath),
        'dimensions': "200x150",
        'color': "Gray"
    })
    
    print(f"✅ Creada: {small_filename} ({os.path.getsize(small_filepath)} bytes)")
    
    return images_created

def create_sample_transformations():
    """Crear ejemplos de transformaciones para pruebas"""
    
    transformations = [
        # Transformación simple - escala de grises
        [
            {
                "tipo": "escala_grises",
                "parametros": {}
            }
        ],
        
        # Transformación múltiple - redimensionar y rotar
        [
            {
                "tipo": "redimensionar",
                "parametros": {
                    "width": 400,
                    "height": 300,
                    "mantener_aspecto": True
                }
            },
            {
                "tipo": "rotar",
                "parametros": {
                    "angulo": 45
                }
            }
        ],
        
        # Transformación compleja
        [
            {
                "tipo": "recortar",
                "parametros": {
                    "x": 100,
                    "y": 100,
                    "width": 600,
                    "height": 400
                }
            },
            {
                "tipo": "brillo_contraste",
                "parametros": {
                    "brillo": 20,
                    "contraste": 15
                }
            },
            {
                "tipo": "marca_agua",
                "parametros": {
                    "texto": "Procesado",
                    "posicion": "bottom-right",
                    "tamaño": 32,
                    "color": "#FF0000"
                }
            }
        ],
        
        # Cambio de formato
        [
            {
                "tipo": "convertir_formato",
                "parametros": {
                    "formato": "jpg"
                }
            }
        ]
    ]
    
    return transformations

if __name__ == "__main__":
    print("🖼️ Creando imágenes de prueba...")
    images = create_test_images()
    
    print(f"\n📋 Imágenes creadas: {len(images)}")
    for img in images:
        print(f"   - {img['filename']}: {img['dimensions']}, {img['size']} bytes, {img['color']}")
    
    print(f"\n🔧 Ejemplos de transformaciones:")
    transformations = create_sample_transformations()
    for i, trans in enumerate(transformations, 1):
        print(f"   {i}. {len(trans)} transformación(es):")
        for t in trans:
            print(f"      - {t['tipo']}")
    
    print(f"\n💡 Las imágenes están listas en: uploads/")
    print("   Puedes usarlas para probar el sistema!")