import threading
from queue import Queue

# Semáforo: Solo 1 persona puede estar frente al lector
semaforo_puerta = threading.Semaphore(1)

# Cola: Canal de comunicación de datos NFC
cola_nfc = Queue()

# Base de datos local de UIDs permitidos
USUARIOS_PERMITIDOS = {
    "99A1": "Admin - Carlos",
    "44B2": "Empleado - Ana",
    "11C3": "Invitado - Luis"
}
