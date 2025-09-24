# Procesador de imágenes usando PIL y OpenCV
import os
import time
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont
import cv2
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import json
import logging
from config import NodoConfig

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self):
        self.supported_formats = NodoConfig.SUPPORTED_FORMATS
        self.max_size = NodoConfig.MAX_IMAGE_SIZE
    
    def process_image(self, image_path: str, output_path: str, transformations: List[Dict]) -> Dict[str, Any]:
        """Procesar una imagen con las transformaciones especificadas"""
        start_time = time.time()
        
        try:
            # Validar archivo de entrada
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Archivo no encontrado: {image_path}")
            
            file_size = os.path.getsize(image_path)
            if file_size > self.max_size:
                raise ValueError(f"Archivo muy grande: {file_size} bytes")
            
            # Cargar imagen
            with Image.open(image_path) as image:
                original_format = image.format
                original_size = image.size
                
                # Aplicar transformaciones secuencialmente
                processed_image = image.copy()
                applied_transformations = []
                
                for transformation in transformations:
                    trans_type = transformation.get('tipo', '').lower()
                    params = transformation.get('parametros', {})
                    
                    try:
                        processed_image = self._apply_transformation(processed_image, trans_type, params)
                        applied_transformations.append({
                            'tipo': trans_type,
                            'parametros': params,
                            'exitoso': True
                        })
                        logger.info(f"Transformación aplicada: {trans_type}")
                        
                    except Exception as e:
                        logger.error(f"Error en transformación {trans_type}: {e}")
                        applied_transformations.append({
                            'tipo': trans_type,
                            'parametros': params,
                            'exitoso': False,
                            'error': str(e)
                        })
                
                # Guardar imagen procesada
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Determinar formato de salida
                output_format = self._get_output_format(output_path, transformations)
                processed_image.save(output_path, format=output_format, quality=95)
                
                # Estadísticas
                processing_time = int((time.time() - start_time) * 1000)
                output_size = os.path.getsize(output_path)
                
                return {
                    'success': True,
                    'message': 'Imagen procesada exitosamente',
                    'processed_image_path': output_path,
                    'stats': {
                        'processing_time_ms': processing_time,
                        'file_size_before': file_size,
                        'file_size_after': output_size,
                        'format_before': original_format,
                        'format_after': output_format,
                        'size_before': original_size,
                        'size_after': processed_image.size
                    },
                    'transformations_applied': applied_transformations,
                    'errors': []
                }
                
        except Exception as e:
            logger.error(f"Error al procesar imagen {image_path}: {e}")
            return {
                'success': False,
                'message': f'Error al procesar imagen: {str(e)}',
                'processed_image_path': None,
                'stats': {
                    'processing_time_ms': int((time.time() - start_time) * 1000),
                    'file_size_before': 0,
                    'file_size_after': 0,
                    'format_before': 'unknown',
                    'format_after': 'unknown'
                },
                'transformations_applied': [],
                'errors': [str(e)]
            }
    
    def _apply_transformation(self, image: Image.Image, trans_type: str, params: Dict) -> Image.Image:
        """Aplicar una transformación específica a la imagen"""
        
        if trans_type == 'escala_grises' or trans_type == 'grayscale':
            return image.convert('L').convert('RGB')
        
        elif trans_type == 'redimensionar' or trans_type == 'resize':
            width = params.get('width', image.width)
            height = params.get('height', image.height)
            mantener_aspecto = params.get('mantener_aspecto', True)
            
            if mantener_aspecto:
                image.thumbnail((width, height), Image.Resampling.LANCZOS)
                return image
            else:
                return image.resize((width, height), Image.Resampling.LANCZOS)
        
        elif trans_type == 'recortar' or trans_type == 'crop':
            x = params.get('x', 0)
            y = params.get('y', 0)
            width = params.get('width', image.width // 2)
            height = params.get('height', image.height // 2)
            
            # Validar coordenadas
            x = max(0, min(x, image.width))
            y = max(0, min(y, image.height))
            width = min(width, image.width - x)
            height = min(height, image.height - y)
            
            return image.crop((x, y, x + width, y + height))
        
        elif trans_type == 'rotar' or trans_type == 'rotate':
            angulo = params.get('angulo', 0)
            return image.rotate(angulo, expand=True, fillcolor='white')
        
        elif trans_type == 'reflejar' or trans_type == 'flip':
            horizontal = params.get('horizontal', False)
            vertical = params.get('vertical', False)
            
            result = image
            if horizontal:
                result = result.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            if vertical:
                result = result.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            
            return result
        
        elif trans_type == 'desenfocar' or trans_type == 'blur':
            radio = params.get('radio', 2.0)
            return image.filter(ImageFilter.GaussianBlur(radius=radio))
        
        elif trans_type == 'nitidez' or trans_type == 'sharpen':
            factor = params.get('factor', 1.5)
            enhancer = ImageEnhance.Sharpness(image)
            return enhancer.enhance(factor)
        
        elif trans_type == 'brillo_contraste' or trans_type == 'brightness_contrast':
            brillo = params.get('brillo', 0) / 100.0  # Convertir porcentaje a factor
            contraste = params.get('contraste', 0) / 100.0
            
            result = image
            
            # Ajustar brillo
            if brillo != 0:
                enhancer = ImageEnhance.Brightness(result)
                result = enhancer.enhance(1 + brillo)
            
            # Ajustar contraste
            if contraste != 0:
                enhancer = ImageEnhance.Contrast(result)
                result = enhancer.enhance(1 + contraste)
            
            return result
        
        elif trans_type == 'marca_agua' or trans_type == 'watermark':
            texto = params.get('texto', 'Marca de Agua')
            posicion = params.get('posicion', 'bottom-right')
            tamaño = params.get('tamaño', 24)
            color = params.get('color', '#FFFFFF')
            
            # Crear una imagen con transparencia para la marca de agua
            overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Intentar cargar una fuente, usar la predeterminada si falla
            try:
                font = ImageFont.truetype("arial.ttf", tamaño)
            except:
                font = ImageFont.load_default()
            
            # Calcular posición del texto
            bbox = draw.textbbox((0, 0), texto, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            positions = {
                'top-left': (10, 10),
                'top-right': (image.width - text_width - 10, 10),
                'bottom-left': (10, image.height - text_height - 10),
                'bottom-right': (image.width - text_width - 10, image.height - text_height - 10),
                'center': ((image.width - text_width) // 2, (image.height - text_height) // 2)
            }
            
            pos = positions.get(posicion, positions['bottom-right'])
            
            # Dibujar texto con transparencia
            draw.text(pos, texto, fill=color + '80', font=font)  # 80 para 50% transparencia
            
            # Combinar con la imagen original
            result = Image.alpha_composite(image.convert('RGBA'), overlay)
            return result.convert('RGB')
        
        elif trans_type == 'convertir_formato' or trans_type == 'convert_format':
            # Esta transformación se maneja en el guardado del archivo
            return image
        
        else:
            logger.warning(f"Transformación no reconocida: {trans_type}")
            return image
    
    def _get_output_format(self, output_path: str, transformations: List[Dict]) -> str:
        """Determinar el formato de salida basado en las transformaciones y la extensión del archivo"""
        
        # Buscar transformación de cambio de formato
        for transformation in transformations:
            if transformation.get('tipo') in ['convertir_formato', 'convert_format']:
                formato = transformation.get('parametros', {}).get('formato', '').lower()
                if formato in ['jpg', 'jpeg']:
                    return 'JPEG'
                elif formato == 'png':
                    return 'PNG'
                elif formato in ['bmp']:
                    return 'BMP'
                elif formato in ['tiff', 'tif']:
                    return 'TIFF'
        
        # Usar extensión del archivo de salida
        ext = os.path.splitext(output_path)[1].lower()
        if ext in ['.jpg', '.jpeg']:
            return 'JPEG'
        elif ext == '.png':
            return 'PNG'
        elif ext == '.bmp':
            return 'BMP'
        elif ext in ['.tiff', '.tif']:
            return 'TIFF'
        
        # Por defecto, usar JPEG
        return 'JPEG'
    
    def validate_transformations(self, transformations: List[Dict]) -> Tuple[bool, List[str]]:
        """Validar que las transformaciones sean válidas"""
        errors = []
        
        valid_types = {
            'escala_grises', 'grayscale',
            'redimensionar', 'resize',
            'recortar', 'crop',
            'rotar', 'rotate',
            'reflejar', 'flip',
            'desenfocar', 'blur',
            'nitidez', 'sharpen',
            'brillo_contraste', 'brightness_contrast',
            'marca_agua', 'watermark',
            'convertir_formato', 'convert_format'
        }
        
        for i, trans in enumerate(transformations):
            trans_type = trans.get('tipo', '').lower()
            
            if trans_type not in valid_types:
                errors.append(f"Transformación {i}: tipo '{trans_type}' no válido")
            
            params = trans.get('parametros', {})
            
            # Validaciones específicas por tipo
            if trans_type in ['redimensionar', 'resize']:
                if 'width' in params and params['width'] <= 0:
                    errors.append(f"Transformación {i}: width debe ser mayor que 0")
                if 'height' in params and params['height'] <= 0:
                    errors.append(f"Transformación {i}: height debe ser mayor que 0")
        
        return len(errors) == 0, errors