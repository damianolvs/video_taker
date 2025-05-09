# capturador.py
"""
Módulo principal para la captura de video desde streams URL.
"""

import cv2
import requests
import numpy as np
import time
import os
from datetime import datetime
import logging
from queue import Queue
from threading import Thread

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("captura_video.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CapturadorVideo")

def configurar_directorios(directorio):
    """Crea los directorios necesarios si no existen."""
    if not os.path.exists(directorio):
        os.makedirs(directorio)
        logger.info(f"Directorio creado: {directorio}")

def generar_nombre_archivo(formato, id_camara, directorio):
    """Genera un nombre de archivo con timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = formato.format(id=id_camara, timestamp=timestamp)
    return os.path.join(directorio, nombre_archivo)

def capturar_video(camara, directorio, formato_nombre):
    """
    Captura video desde una URL y lo guarda en formato MP4.
    
    Args:
        camara (dict): Diccionario con la configuración de la cámara
        directorio (str): Directorio donde guardar el video
        formato_nombre (str): Formato para el nombre del archivo
        
    Returns:
        tuple: (éxito, nombre_archivo, mensaje)
    """
    # Extraer información de la cámara
    id_camara = camara["id"]
    nombre_camara = camara["nombre"]
    url = camara["url"]
    duracion = camara.get("duracion", 30)  # Valor predeterminado: 30 segundos
    fps = camara.get("fps", 20)  # Valor predeterminado: 20 FPS
    
    # Generar nombre de archivo
    output_filename = generar_nombre_archivo(formato_nombre, id_camara, directorio)
    
    logger.info(f"Iniciando captura desde {nombre_camara} (ID: {id_camara})")
    logger.info(f"URL: {url}")
    logger.info(f"Archivo de salida: {output_filename}")
    logger.info(f"Duración: {duracion} segundos, FPS: {fps}")
    
    try:
        # Iniciar sesión para el stream
        session = requests.Session()
        response = session.get(url, stream=True, timeout=10)
        
        if response.status_code != 200:
            mensaje = f"Error al conectar a la URL de {nombre_camara}: Código {response.status_code}"
            logger.error(mensaje)
            return False, output_filename, mensaje
        
        # Configurar el codificador para MP4
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        
        # Variables para controlar el tamaño y la escritura
        frame_size = None
        out = None
        bytes_data = bytes()
        
        start_time = time.time()
        frames_captured = 0
        
        # Bucle de captura
        while time.time() - start_time < duracion:
            # Leer datos del stream
            chunk = response.raw.read(1024)
            if not chunk:
                break
                
            bytes_data += chunk
            
            # Buscar inicio de un frame JPEG en el stream
            a = bytes_data.find(b'\xff\xd8')
            b = bytes_data.find(b'\xff\xd9')
            
            # Si tenemos un frame completo
            if a != -1 and b != -1:
                jpg_data = bytes_data[a:b+2]
                bytes_data = bytes_data[b+2:]
                
                # Decodificar bytes a imagen
                frame = cv2.imdecode(np.frombuffer(jpg_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                
                if frame is not None:
                    # Configurar el escritor de video con el primer frame
                    if frame_size is None:
                        frame_size = (frame.shape[1], frame.shape[0])
                        out = cv2.VideoWriter(output_filename, fourcc, fps, frame_size)
                        logger.info(f"Tamaño de frame detectado para {nombre_camara}: {frame_size}")
                    
                    # Escribir el frame al archivo de video
                    out.write(frame)
                    frames_captured += 1
                    
                    # Mostrar avance periódicamente
                    if frames_captured % fps == 0:
                        elapsed = time.time() - start_time
                        logger.info(f"{nombre_camara}: Capturado {frames_captured} frames ({elapsed:.2f} segundos)")
        
        # Liberar recursos
        if out is not None:
            out.release()
            logger.info(f"Video de {nombre_camara} guardado como {output_filename}")
            logger.info(f"Total de frames capturados: {frames_captured}")
            return True, output_filename, f"Captura completada: {frames_captured} frames"
        else:
            mensaje = f"No se pudo iniciar la captura de video para {nombre_camara}. Verifique la URL."
            logger.error(mensaje)
            return False, output_filename, mensaje
            
    except requests.exceptions.RequestException as e:
        mensaje = f"Error de conexión para {nombre_camara}: {str(e)}"
        logger.error(mensaje)
        return False, output_filename, mensaje
    except Exception as e:
        mensaje = f"Error durante la captura de {nombre_camara}: {str(e)}"
        logger.error(mensaje)
        return False, output_filename, mensaje

def worker_captura(queue, directorio, formato_nombre, resultados):
    """Función worker para procesar cámaras en hilos paralelos."""
    while not queue.empty():
        try:
            camara = queue.get()
            exito, archivo, mensaje = capturar_video(camara, directorio, formato_nombre)
            resultados.append({
                "id": camara["id"],
                "nombre": camara["nombre"],
                "exito": exito,
                "archivo": archivo,
                "mensaje": mensaje
            })
        except Exception as e:
            logger.error(f"Error en worker de captura: {str(e)}")
        finally:
            queue.task_done()

def capturar_todas_las_camaras(camaras, directorio, formato_nombre, max_hilos=4):
    """
    Captura video de múltiples cámaras en paralelo.
    
    Args:
        camaras (list): Lista de diccionarios con configuración de cámaras
        directorio (str): Directorio donde guardar los videos
        formato_nombre (str): Formato para nombres de archivos
        max_hilos (int): Número máximo de hilos en paralelo
        
    Returns:
        list: Lista de resultados por cámara
    """
    if not camaras:
        logger.warning("No hay cámaras habilitadas para capturar")
        return []
    
    # Crear directorio si no existe
    configurar_directorios(directorio)
    
    # Cola de trabajo y resultados
    queue = Queue()
    resultados = []
    
    # Agregar cámaras a la cola
    for camara in camaras:
        queue.put(camara)
    
    # Limitar hilos al número de cámaras si es necesario
    num_hilos = min(max_hilos, len(camaras))
    
    # Crear y lanzar hilos
    logger.info(f"Iniciando captura con {num_hilos} hilos paralelos")
    hilos = []
    for _ in range(num_hilos):
        t = Thread(target=worker_captura, args=(queue, directorio, formato_nombre, resultados))
        t.daemon = True
        t.start()
        hilos.append(t)
    
    # Esperar a que terminen todos los hilos
    queue.join()
    
    return resultados