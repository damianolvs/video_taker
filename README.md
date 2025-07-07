README.md - Servidor de Captura de Video
Descripción
Este proyecto permite capturar video desde múltiples cámaras IP o URL de streams y guardarlo localmente. Incluye una API REST para controlar la captura de forma remota.

Requisitos
Python 3.12+
Poetry (para gestión de dependencias)
Cámaras IP accesibles mediante URL
Instalación
1. Instalar dependencias con Poetry
bash
# Instalar Poetry si no está instalado
curl -sSL https://install.python-poetry.org | python3 -

# Instalar dependencias del proyecto
poetry install
2. Configurar las cámaras
Edita el archivo config.py para configurar las cámaras:

python
CAMARAS = [
    {
        "id": "cam1",
        "nombre": "Cámara Principal",
        "url": "http://IP_DE_TU_CAMARA:PUERTO/video_feed",
        "duracion": 30,
        "fps": 30,
        "habilitada": True
    },
    # Añade más cámaras según sea necesario
]
Ejecución
Iniciar el servidor
bash
# Entrar en el entorno virtual de Poetry
poetry shell

# Iniciar el servidor
python server.py
El servidor estará disponible en:

API: http://IP_DE_TU_SERVIDOR:8000
Documentación API: http://IP_DE_TU_SERVIDOR:8000/docs
Videos: http://IP_DE_TU_SERVIDOR:8000/videos
Usar como servicio (Linux)
Para que el servidor siga funcionando incluso cuando cierres la terminal o te desconectes:

Crear un archivo de servicio systemd:
bash
sudo nano /etc/systemd/system/video-capture.service
Añadir el siguiente contenido (ajusta las rutas según tu instalación):
[Unit]
Description=Servidor de Captura de Video
After=network.target

[Service]
User=tu_usuario
WorkingDirectory=/ruta/a/tu/proyecto
ExecStart=/ruta/a/poetry/bin/poetry run python server.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
Habilitar e iniciar el servicio:
bash
sudo systemctl enable video-capture.service
sudo systemctl start video-capture.service
Verificar el estado:
bash
sudo systemctl status video-capture.service
API REST
Endpoints principales
Método	Ruta	Descripción
GET	/camaras	Lista todas las cámaras configuradas
GET	/camaras/{id_camara}	Obtiene información de una cámara específica
PUT	/camaras/{id_camara}	Actualiza configuración de una cámara
POST	/capturar	Inicia la captura de todas las cámaras habilitadas
POST	/capturar/{id_camara}	Inicia la captura de una cámara específica
GET	/estado/{task_id}	Consulta el estado de una tarea de captura
GET	/formato	Obtiene el formato de video configurado
PUT	/formato/{formato}	Cambia el formato de video (mp4/avi)
Consulta la documentación completa en http://IP_DE_TU_SERVIDOR:8000/docs

Formatos de Video
AVI (por defecto): Sin compresión, alta calidad pero archivos grandes
MP4: Con compresión, archivos más pequeños pero menor calidad
Estructura del Proyecto
server.py: Punto de entrada principal del servidor
api.py: Implementación de la API REST
config.py: Configuración de cámaras y opciones
capturador.py: Módulo para capturar video
videos_capturados/: Directorio donde se guardan los videos
reportes/: Directorio donde se guardan los reportes de captura
