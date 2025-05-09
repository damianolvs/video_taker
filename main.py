# main.py
"""
Script principal para ejecutar la captura de video de múltiples cámaras.
"""

import argparse
import time
from datetime import datetime
import os
import json

# Importar módulos propios
from config import (
    CAMARAS, 
    DIRECTORIO_VIDEOS, 
    FORMATO_NOMBRE, 
    obtener_camaras_habilitadas,
    obtener_camara_por_id,
    cambiar_estado_camara
)
from capturador import capturar_video, capturar_todas_las_camaras

def mostrar_camaras():
    """Muestra la lista de cámaras configuradas."""
    print("\n=== CÁMARAS CONFIGURADAS ===")
    print(f"{'ID':<10} {'NOMBRE':<25} {'HABILITADA':<10} {'URL'}")
    print("-" * 80)
    
    for camara in CAMARAS:
        habilitada = "Sí" if camara.get("habilitada", True) else "No"
        print(f"{camara['id']:<10} {camara['nombre']:<25} {habilitada:<10} {camara['url']}")
    
    print("-" * 80)
    print(f"Total: {len(CAMARAS)} cámaras, {len(obtener_camaras_habilitadas())} habilitadas\n")

def guardar_resultados(resultados):
    """Guarda los resultados de la captura en un archivo JSON."""
    # Crear directorio de reportes si no existe
    directorio_reportes = "reportes"
    if not os.path.exists(directorio_reportes):
        os.makedirs(directorio_reportes)
    
    # Generar nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_reporte = os.path.join(directorio_reportes, f"captura_{timestamp}.json")
    
    # Crear un diccionario con información del reporte
    reporte = {
        "fecha": datetime.now().isoformat(),
        "total_camaras": len(resultados),
        "exitosas": sum(1 for r in resultados if r["exito"]),
        "fallidas": sum(1 for r in resultados if not r["exito"]),
        "resultados": resultados
    }
    
    # Guardar como JSON
    with open(archivo_reporte, 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    
    print(f"Reporte guardado en: {archivo_reporte}")
    return archivo_reporte

def main():
    """Función principal del programa."""
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Capturador de video desde múltiples cámaras")
    parser.add_argument('-l', '--listar', action='store_true', help='Listar cámaras configuradas')
    parser.add_argument('-c', '--capturar', action='store_true', help='Iniciar captura de todas las cámaras habilitadas')
    parser.add_argument('-s', '--single', metavar='ID_CAMARA', help='Capturar de una sola cámara por su ID')
    parser.add_argument('-e', '--enable', metavar='ID_CAMARA', help='Habilitar una cámara por su ID')
    parser.add_argument('-d', '--disable', metavar='ID_CAMARA', help='Deshabilitar una cámara por su ID')
    parser.add_argument('-p', '--paralelo', type=int, default=4, help='Número máximo de hilos paralelos (por defecto: 4)')
    
    args = parser.parse_args()
    
    # Mostrar información del programa
    print("\n=== CAPTURADOR DE VIDEO DESDE URL ===")
    print(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Directorio de videos: {DIRECTORIO_VIDEOS}")
    
    # Procesar argumentos
    if args.listar or (not args.capturar and not args.single and not args.enable and not args.disable):
        mostrar_camaras()
    
    # Habilitar/deshabilitar cámaras
    if args.enable:
        if cambiar_estado_camara(args.enable, True):
            print(f"Cámara {args.enable} habilitada correctamente")
        else:
            print(f"Error: No se encontró la cámara con ID {args.enable}")
    
    if args.disable:
        if cambiar_estado_camara(args.disable, False):
            print(f"Cámara {args.disable} deshabilitada correctamente")
        else:
            print(f"Error: No se encontró la cámara con ID {args.disable}")
    
    # Capturar de una sola cámara
    if args.single:
        camara = obtener_camara_por_id(args.single)
        if not camara:
            print(f"Error: No se encontró la cámara con ID {args.single}")
            return
        
        print(f"\nIniciando captura de la cámara: {camara['nombre']} (ID: {camara['id']})")
        print(f"URL: {camara['url']}")
        
        inicio = time.time()
        exito, archivo, mensaje = capturar_video(camara, DIRECTORIO_VIDEOS, FORMATO_NOMBRE)
        duracion = time.time() - inicio
        
        print(f"\nResultado para {camara['nombre']}:")
        print(f"  {'Éxito' if exito else 'Error'}: {mensaje}")
        print(f"  Archivo: {archivo}")
        print(f"  Tiempo total: {duracion:.2f} segundos")
    
    # Capturar de todas las cámaras habilitadas
    if args.capturar:
        camaras_habilitadas = obtener_camaras_habilitadas()
        if not camaras_habilitadas:
            print("No hay cámaras habilitadas para capturar.")
            return
        
        print(f"\nIniciando captura de {len(camaras_habilitadas)} cámaras habilitadas...")
        print(f"Usando {args.paralelo} hilos en paralelo")
        
        inicio = time.time()
        resultados = capturar_todas_las_camaras(
            camaras_habilitadas, 
            DIRECTORIO_VIDEOS, 
            FORMATO_NOMBRE,
            max_hilos=args.paralelo
        )
        duracion = time.time() - inicio
        
        # Mostrar resultados
        print("\n=== RESULTADOS DE CAPTURA ===")
        print(f"{'ID':<10} {'NOMBRE':<25} {'ESTADO':<10} {'ARCHIVO'}")
        print("-" * 80)
        
        for resultado in resultados:
            estado = "Éxito" if resultado["exito"] else "Error"
            print(f"{resultado['id']:<10} {resultado['nombre']:<25} {estado:<10} {os.path.basename(resultado['archivo'])}")
        
        print("-" * 80)
        print(f"Total: {len(resultados)} cámaras procesadas")
        print(f"Éxito: {sum(1 for r in resultados if r['exito'])} cámaras")
        print(f"Error: {sum(1 for r in resultados if not r['exito'])} cámaras")
        print(f"Tiempo total: {duracion:.2f} segundos")
        
        # Guardar reporte
        guardar_resultados(resultados)

if __name__ == "__main__":
    main()