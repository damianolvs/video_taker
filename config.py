# config.py
"""
Archivo de configuración para las cámaras de vigilancia.
Cada cámara debe tener un identificador único y una URL de stream.
"""

import os

# Duración predeterminada de captura para todas las cámaras (en segundos)
DURACION_PREDETERMINADA = 30

# FPS predeterminados para la grabación
FPS_PREDETERMINADOS = 30

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

# Configuración de formato de video
# Formatos disponibles: 'mp4' (comprimido) o 'avi' (sin compresión)
FORMATO_VIDEO = "avi"  # Valor por defecto: 'avi' sin compresión

# Codecs disponibles por formato
CODECS = {
    "mp4": "mp4v",  # Codec para MP4 (comprimido)
    "avi": "I420"   # Codec para AVI (sin compresión)
}

# Formato de nombres de archivos (se agregará fecha/hora automáticamente)
# La extensión se ajustará automáticamente según FORMATO_VIDEO
FORMATO_NOMBRE = "camara_{id}_{timestamp}.{ext}"

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
        "fps": 30,
        "habilitada": True
    }
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

# Función para cambiar el formato de video
def cambiar_formato_video(formato):
    """
    Cambia el formato de video para todas las capturas.
    
    Args:
        formato (str): Formato de video ('mp4' o 'avi')
        
    Returns:
        bool: True si el formato es válido, False en caso contrario
    """
    formatos_validos = list(CODECS.keys())
    
    if formato.lower() not in formatos_validos:
        print(f"Error: Formato no válido. Formatos disponibles: {', '.join(formatos_validos)}")
        return False
    
    global FORMATO_VIDEO
    FORMATO_VIDEO = formato.lower()
    print(f"Formato de video cambiado a: {FORMATO_VIDEO}")
    print(f"Codec utilizado: {CODECS[FORMATO_VIDEO]}")
    return True

# Función para obtener la extensión de archivo según el formato de video actual
def obtener_extension():
    """Retorna la extensión de archivo según el formato de video configurado."""
    return FORMATO_VIDEO

# Función para obtener el codec según el formato de video actual
def obtener_codec():
    """Retorna el código de codec según el formato de video configurado."""
    return CODECS[FORMATO_VIDEO]