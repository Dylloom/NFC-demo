import threading
from queue import Queue

# Semáforo para el cerrojo físico
semaforo_nfc = threading.Semaphore(1)
# Cola para enviar mensajes desde el hilo de hardware a la interfaz
cola_mensajes = Queue()

# Credenciales y Configuración
USER_DB = {"admin": "1234", "andy": "tonotos67"}
TITULO_APP = "MiTaller"
