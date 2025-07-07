# api.py
"""
API REST para el capturador de video desde múltiples cámaras.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import json
from datetime import datetime

# Importar módulos propios
from config import (
    CAMARAS, 
    DIRECTORIO_VIDEOS, 
    FORMATO_NOMBRE,
    obtener_camaras_habilitadas,
    obtener_camara_por_id,
    cambiar_estado_camara,
    cambiar_formato_video,
    obtener_extension,
    obtener_codec,
    actualizar_url_camara
)
from capturador import capturar_video, capturar_todas_las_camaras

# Crear la aplicación FastAPI
app = FastAPI(
    title="API de Captura de Video",
    description="API para gestionar la captura de video desde múltiples cámaras",
    version="1.0.0"
)

# Configurar CORS para permitir acceso desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes (puedes restringirlo en producción)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de datos para la API
class Camara(BaseModel):
    id: str
    nombre: str
    url: str
    duracion: Optional[int] = 30
    fps: Optional[int] = 30
    habilitada: Optional[bool] = True

class ResultadoCaptura(BaseModel):
    id: str
    nombre: str
    exito: bool
    archivo: str
    mensaje: str

class ActualizarCamara(BaseModel):
    url: Optional[str] = None
    nombre: Optional[str] = None
    duracion: Optional[int] = None
    fps: Optional[int] = None
    habilitada: Optional[bool] = None

# Variable para mantener estado de tareas en progreso
tareas_activas = {}

# Funciones auxiliares
def guardar_resultados(resultados):
    """Guarda los resultados de la captura en un archivo JSON."""
    # Crear directorio de reportes si no existe
    directorio_reportes = "reportes"
    if not os.path.exists(directorio_reportes):
        os.makedirs(directorio_reportes)
    
    # Generar nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_reporte = os.path.join(directorio_reportes, f"captura_{timestamp}.json")
    
    # Obtener información del formato actual
    formato = obtener_extension().upper()
    codec = obtener_codec()
    
    # Crear un diccionario con información del reporte
    reporte = {
        "fecha": datetime.now().isoformat(),
        "total_camaras": len(resultados),
        "exitosas": sum(1 for r in resultados if r["exito"]),
        "fallidas": sum(1 for r in resultados if not r["exito"]),
        "formato_video": f"{formato} ({codec})",
        "resultados": resultados
    }
    
    # Guardar como JSON
    with open(archivo_reporte, 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    
    return archivo_reporte, reporte

def background_capture_all(task_id: str, max_hilos: int = 4):
    """Función para ejecutar captura en segundo plano"""
    camaras_habilitadas = obtener_camaras_habilitadas()
    if not camaras_habilitadas:
        tareas_activas[task_id] = {"estado": "error", "mensaje": "No hay cámaras habilitadas para capturar."}
        return
    
    try:
        # Cambiar estado a "en progreso"
        tareas_activas[task_id] = {"estado": "en_progreso", "progreso": 0}
        
        # Realizar captura
        resultados = capturar_todas_las_camaras(
            camaras_habilitadas, 
            DIRECTORIO_VIDEOS, 
            FORMATO_NOMBRE,
            max_hilos=max_hilos
        )
        
        # Guardar resultados
        archivo_reporte, reporte = guardar_resultados(resultados)
        
        # Actualizar estado a "completado"
        tareas_activas[task_id] = {
            "estado": "completado", 
            "reporte": reporte,
            "archivo_reporte": archivo_reporte
        }
    except Exception as e:
        # Registrar error
        tareas_activas[task_id] = {"estado": "error", "mensaje": str(e)}

# Rutas de la API

@app.get("/")
async def root():
    """Ruta raíz que muestra información básica de la API"""
    return {
        "nombre": "API de Captura de Video",
        "version": "1.0.0",
        "endpoints": [
            "/camaras",
            "/camaras/{id_camara}",
            "/capturar",
            "/capturar/{id_camara}",
            "/estado/{task_id}",
            "/formato",
        ]
    }

@app.get("/camaras", response_model=List[Camara])
async def listar_camaras():
    """Obtiene la lista de todas las cámaras configuradas"""
    return CAMARAS

@app.get("/camaras/{id_camara}", response_model=Camara)
async def obtener_camara(id_camara: str):
    """Obtiene la información de una cámara específica por su ID"""
    camara = obtener_camara_por_id(id_camara)
    if not camara:
        raise HTTPException(status_code=404, detail=f"Cámara con ID {id_camara} no encontrada")
    return camara

@app.put("/camaras/{id_camara}")
async def actualizar_camara(id_camara: str, datos: ActualizarCamara):
    """Actualiza la información de una cámara específica"""
    camara = obtener_camara_por_id(id_camara)
    if not camara:
        raise HTTPException(status_code=404, detail=f"Cámara con ID {id_camara} no encontrada")
    
    # Actualizar campos proporcionados
    for i, c in enumerate(CAMARAS):
        if c["id"] == id_camara:
            if datos.url is not None:
                CAMARAS[i]["url"] = datos.url
            if datos.nombre is not None:
                CAMARAS[i]["nombre"] = datos.nombre
            if datos.duracion is not None:
                CAMARAS[i]["duracion"] = datos.duracion
            if datos.fps is not None:
                CAMARAS[i]["fps"] = datos.fps
            if datos.habilitada is not None:
                CAMARAS[i]["habilitada"] = datos.habilitada
            return CAMARAS[i]
    
    # Este código no debería ejecutarse si ya encontramos la cámara arriba
    raise HTTPException(status_code=500, detail="Error al actualizar la cámara")

@app.post("/capturar")
async def capturar_todas(background_tasks: BackgroundTasks, max_hilos: int = Query(4, ge=1, le=16)):
    """Inicia la captura de todas las cámaras habilitadas en segundo plano"""
    # Crear un ID único para la tarea
    task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Iniciar tarea en segundo plano
    background_tasks.add_task(background_capture_all, task_id, max_hilos)
    
    # Registrar tarea como pendiente
    tareas_activas[task_id] = {"estado": "pendiente"}
    
    return {"message": "Captura iniciada en segundo plano", "task_id": task_id}

@app.post("/capturar/{id_camara}")
async def capturar_una_camara(id_camara: str):
    """Captura video de una cámara específica"""
    camara = obtener_camara_por_id(id_camara)
    if not camara:
        raise HTTPException(status_code=404, detail=f"Cámara con ID {id_camara} no encontrada")
    
    if not camara.get("habilitada", True):
        raise HTTPException(status_code=400, detail=f"La cámara {id_camara} está deshabilitada")
    
    # Realizar captura (síncrona en este caso para una sola cámara)
    exito, archivo, mensaje = capturar_video(camara, DIRECTORIO_VIDEOS, FORMATO_NOMBRE)
    
    # Obtener tamaño del archivo si fue exitoso
    tamano_mb = 0
    if exito and os.path.exists(archivo):
        tamano_mb = os.path.getsize(archivo) / (1024 * 1024)  # Tamaño en MB
    
    return {
        "id": camara["id"],
        "nombre": camara["nombre"],
        "exito": exito,
        "archivo": archivo,
        "mensaje": mensaje,
        "tamano_mb": round(tamano_mb, 2)
    }

@app.get("/estado/{task_id}")
async def obtener_estado_tarea(task_id: str):
    """Obtiene el estado actual de una tarea de captura"""
    if task_id not in tareas_activas:
        raise HTTPException(status_code=404, detail=f"Tarea con ID {task_id} no encontrada")
    
    return tareas_activas[task_id]

@app.get("/formato")
async def obtener_formato():
    """Obtiene el formato de video configurado actualmente"""
    return {
        "formato": obtener_extension(),
        "codec": obtener_codec(),
        "es_comprimido": obtener_extension().lower() == 'mp4'
    }

@app.put("/formato/{formato}")
async def cambiar_formato(formato: str):
    """Cambia el formato de video para las capturas futuras"""
    if formato.lower() not in ["mp4", "avi"]:
        raise HTTPException(status_code=400, detail="Formato no válido. Use 'mp4' o 'avi'")
    
    resultado = cambiar_formato_video(formato)
    
    return {
        "mensaje": f"Formato cambiado a {formato}",
        "formato": obtener_extension(),
        "codec": obtener_codec(),
        "es_comprimido": obtener_extension().lower() == 'mp4'
    }

# Punto de entrada para uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)