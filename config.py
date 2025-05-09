# configuracion.py
"""
Archivo de configuración para las cámaras de vigilancia.
Cada cámara debe tener un identificador único y una URL de stream.
"""

import os

# Duración predeterminada de captura para todas las cámaras (en segundos)
DURACION_PREDETERMINADA = 30

# FPS predeterminados para la grabación
FPS_PREDETERMINADOS = 20

# Directorio donde se guardarán los videos
DIRECTORIO_VIDEOS = "videos_capturados"

# Crear el directorio para videos si no existe
def crear_directorio_videos():
    """Crea el directorio para videos si no existe."""
    if not os.path.exists(DIRECTORIO_VIDEOS):
        try:
            os.makedirs(DIRECTORIO_VIDEOS)
            print(f"Directorio creado: {DIRECTORIO_VIDEOS}")
        except Exception as e:
            print(f"Error al crear directorio {DIRECTORIO_VIDEOS}: {str(e)}")
    return os.path.exists(DIRECTORIO_VIDEOS)

# Crear el directorio al importar este módulo
crear_directorio_videos()

# Formato de nombres de archivos (se agregará fecha/hora automáticamente)
FORMATO_NOMBRE = "camara_{id}_{timestamp}.mp4"

# Lista de cámaras configuradas
# Cada cámara es un diccionario con:
# - id: identificador único para la cámara (string)
# - nombre: nombre descriptivo de la cámara (string)
# - url: URL del stream de video (string)
# - duracion: duración en segundos para esta cámara específica (opcional, int)
# - fps: frames por segundo para esta cámara específica (opcional, int)
# - habilitada: indica si esta cámara debe ser incluida en la captura (bool)

CAMARAS = [
    {
        "id": "cam1",
        "nombre": "Cámara Principal",
        "url": "http://10.137.140.97:8000/video_feed",
        "duracion": 30,
        "fps": 20,
        "habilitada": True
    },
    # Agrega más cámaras según sea necesario, por ejemplo:
    {
        "id": "cam2",
        "nombre": "Cámara Secundaria",
        "url": "http://example.com/camera2/stream",
        "duracion": 60,  # Esta cámara grabará por 60 segundos
        "fps": 15,       # A 15 FPS
        "habilitada": False  # Esta cámara está deshabilitada por defecto
    },
]

# Función para obtener solo las cámaras habilitadas
def obtener_camaras_habilitadas():
    """Retorna una lista con solo las cámaras que están habilitadas."""
    return [camara for camara in CAMARAS if camara.get("habilitada", True)]

# Función para obtener una cámara por su ID
def obtener_camara_por_id(id_camara):
    """Busca y retorna una cámara por su ID."""
    for camara in CAMARAS:
        if camara["id"] == id_camara:
            return camara
    return None

# Función para habilitar/deshabilitar una cámara
def cambiar_estado_camara(id_camara, habilitar=True):
    """Cambia el estado de habilitación de una cámara."""
    for i, camara in enumerate(CAMARAS):
        if camara["id"] == id_camara:
            CAMARAS[i]["habilitada"] = habilitar
            return True
    return False

# Función para actualizar la URL de una cámara
def actualizar_url_camara(id_camara, nueva_url):
    """Actualiza la URL de una cámara específica."""
    for i, camara in enumerate(CAMARAS):
        if camara["id"] == id_camara:
            CAMARAS[i]["url"] = nueva_url
            return True
    return False