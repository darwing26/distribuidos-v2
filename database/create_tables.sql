-- Script para crear la base de datos del sistema de procesamiento de imágenes
-- Base de datos: sistema_imagenes

DROP DATABASE IF EXISTS sistema_imagenes;
CREATE DATABASE sistema_imagenes CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sistema_imagenes;

-- Tabla de usuarios
CREATE TABLE usuarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE,
    INDEX idx_username (username),
    INDEX idx_email (email)
);

-- Tabla de nodos trabajadores
CREATE TABLE nodos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    identificador VARCHAR(50) UNIQUE NOT NULL,
    direccion_ip VARCHAR(45) NOT NULL,
    puerto INT NOT NULL,
    estado ENUM('activo', 'inactivo', 'error') DEFAULT 'inactivo',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    descripcion TEXT,
    INDEX idx_estado (estado),
    INDEX idx_identificador (identificador)
);

-- Tabla de solicitudes (lotes)
CREATE TABLE solicitudes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('pendiente', 'procesando', 'completado', 'error') DEFAULT 'pendiente',
    total_imagenes INT DEFAULT 0,
    imagenes_procesadas INT DEFAULT 0,
    fecha_completado TIMESTAMP NULL,
    descripcion TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_usuario_id (usuario_id),
    INDEX idx_estado (estado),
    INDEX idx_fecha_solicitud (fecha_solicitud)
);

-- Tabla de transformaciones disponibles
CREATE TABLE transformaciones (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    descripcion TEXT,
    parametros_schema JSON,
    activo BOOLEAN DEFAULT TRUE,
    INDEX idx_nombre (nombre)
);

-- Tabla de imágenes
CREATE TABLE imagenes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    solicitud_id INT NOT NULL,
    nombre_original VARCHAR(255) NOT NULL,
    ruta_original VARCHAR(500) NOT NULL,
    ruta_procesada VARCHAR(500),
    formato_original VARCHAR(10),
    formato_destino VARCHAR(10),
    tamaño_original BIGINT,
    tamaño_procesado BIGINT,
    fecha_recepcion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_inicio_procesamiento TIMESTAMP NULL,
    fecha_fin_procesamiento TIMESTAMP NULL,
    nodo_id INT,
    estado ENUM('pendiente', 'procesando', 'completado', 'error') DEFAULT 'pendiente',
    transformaciones_solicitadas JSON,
    transformaciones_aplicadas JSON,
    mensaje_error TEXT,
    FOREIGN KEY (solicitud_id) REFERENCES solicitudes(id) ON DELETE CASCADE,
    FOREIGN KEY (nodo_id) REFERENCES nodos(id) ON DELETE SET NULL,
    INDEX idx_solicitud_id (solicitud_id),
    INDEX idx_estado (estado),
    INDEX idx_nodo_id (nodo_id),
    INDEX idx_fecha_recepcion (fecha_recepcion)
);

-- Tabla de logs del sistema
CREATE TABLE logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nivel ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL') NOT NULL,
    mensaje TEXT NOT NULL,
    modulo VARCHAR(100),
    funcion VARCHAR(100),
    linea INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_id INT,
    solicitud_id INT,
    imagen_id INT,
    nodo_id INT,
    datos_adicionales JSON,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    FOREIGN KEY (solicitud_id) REFERENCES solicitudes(id) ON DELETE SET NULL,
    FOREIGN KEY (imagen_id) REFERENCES imagenes(id) ON DELETE SET NULL,
    FOREIGN KEY (nodo_id) REFERENCES nodos(id) ON DELETE SET NULL,
    INDEX idx_nivel (nivel),
    INDEX idx_timestamp (timestamp),
    INDEX idx_modulo (modulo),
    INDEX idx_usuario_id (usuario_id),
    INDEX idx_solicitud_id (solicitud_id)
);

-- Insertar transformaciones disponibles
INSERT INTO transformaciones (nombre, descripcion, parametros_schema) VALUES
('escala_grises', 'Conversión a escala de grises', '{}'),
('redimensionar', 'Cambiar el tamaño de la imagen', '{"width": "int", "height": "int", "mantener_aspecto": "bool"}'),
('recortar', 'Recortar una región de la imagen', '{"x": "int", "y": "int", "width": "int", "height": "int"}'),
('rotar', 'Rotar la imagen', '{"angulo": "float"}'),
('reflejar', 'Reflejar la imagen', '{"horizontal": "bool", "vertical": "bool"}'),
('desenfocar', 'Aplicar desenfoque', '{"radio": "float"}'),
('nitidez', 'Aplicar filtro de nitidez', '{"factor": "float"}'),
('brillo_contraste', 'Ajustar brillo y contraste', '{"brillo": "float", "contraste": "float"}'),
('marca_agua', 'Insertar marca de agua o texto', '{"texto": "string", "posicion": "string", "tamaño": "int", "color": "string"}'),
('convertir_formato', 'Convertir formato de imagen', '{"formato": "string"}');

-- Insertar usuario de prueba (password: admin123)
INSERT INTO usuarios (username, email, password_hash) VALUES
('admin', 'admin@sistema.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewvhZlKScAA6eq6.'),
('testuser', 'test@sistema.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewvhZlKScAA6eq6.');

-- Insertar nodos de prueba
INSERT INTO nodos (identificador, direccion_ip, puerto, descripcion) VALUES
('nodo-001', '127.0.0.1', 50051, 'Nodo de procesamiento principal'),
('nodo-002', '127.0.0.1', 50052, 'Nodo de procesamiento secundario'),
('nodo-003', '127.0.0.1', 50053, 'Nodo de procesamiento terciario');

-- Crear índices adicionales para optimizar consultas
CREATE INDEX idx_imagenes_estado_fecha ON imagenes(estado, fecha_recepcion);
CREATE INDEX idx_logs_timestamp_nivel ON logs(timestamp, nivel);
CREATE INDEX idx_solicitudes_usuario_fecha ON solicitudes(usuario_id, fecha_solicitud);

COMMIT;