import threading
from queue import Queue

# -------------------------------------------------------------
# 3 MÉTODOS DE COMUNICACIÓN ENTRE PROCESOS / HILOS (IPC)
# -------------------------------------------------------------
# IPC Método 1: Semáforo para control de acceso físico (hardware NFC/Puerta)
semaforo_nfc = threading.Semaphore(1)

# IPC Método 2: Cola de mensajes (Queue) Hilo Secundario -> Hilo Principal de la GUI
cola_mensajes = Queue()

# IPC Método 3: Mutex (Lock) para sincronización de escritura en archivos (.txt)
lock_chat = threading.Lock()

# Configuración de Red TCP
HOST_CHAT = "127.0.0.1"
PORT_CHAT = 5555
TITULO_APP = "MiTaller - Control de Acceso y Chat Multicanal"
