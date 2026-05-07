import threading
import time
from config import semaforo_puerta, cola_nfc

class PersonaConNFC(threading.Thread):
    def __init__(self, nombre, uid):
        super().__init__()
        self.nombre = nombre
        self.uid = uid

    def run(self):
        print(f"  [PERSONA] {self.nombre} ha llegado a la puerta.")
        
        # El semáforo asegura que entren "uno a la vez"
        with semaforo_puerta:
            print(f"  [NFC] {self.nombre} acerca su móvil al lector...")
            
            # Enviamos el UID a la cola (simulación de transferencia por inducción)
            datos = {'uid': self.uid, 'nombre': self.nombre}
            cola_nfc.put(datos)
            
            # Esperamos a que el lector termine de procesar antes de retirarnos
            cola_nfc.join()
            print(f"  [NFC] {self.nombre} se ha retirado de la zona de lectura.")
