import threading
import time
from config import cola_nfc, USUARIOS_PERMITIDOS

class LectorNFC(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.activo = True

    def run(self):
        print("[SISTEMA] Lector de puerta iniciado y en espera...")
        while self.activo:
            # Espera a que alguien ponga datos en la cola
            paquete = cola_nfc.get()
            uid = paquete['uid']
            
            print(f"[LECTOR] Escaneando dispositivo...")
            time.sleep(1)  # Simula el tiempo de lectura del chip
            
            if uid in USUARIOS_PERMITIDOS:
                nombre = USUARIOS_PERMITIDOS[uid]
                print(f"[LECTOR] ✅ Acceso concedido: {nombre}. Abriendo cerrojo...")
            else:
                print(f"[LECTOR] ❌ Acceso denegado: UID {uid} desconocido.")
            
            print("[SISTEMA] Cerrando puerta y rearmando... \n")
            cola_nfc.task_done()
