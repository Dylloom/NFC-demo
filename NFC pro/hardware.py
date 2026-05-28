import time
import sqlite3
from config import semaforo_nfc, cola_mensajes
from registro import registrar_acceso
from database import DB_NAME

def simulacion_nfc_thread(usuario, forzar_fallo=False):
    """Hilo encargado del hardware. Soporta simulación de denegación de acceso."""
    with semaforo_nfc:
        cola_mensajes.put("Acercar a la puerta")
        time.sleep(1.2)
        
        cola_mensajes.put("Leyendo NFC...")
        time.sleep(1.2)
        
        if forzar_fallo:
            # Flujo de Error: No se invoca a registrar_acceso()
            cola_mensajes.put("ERROR: Acceso Denegado")
            time.sleep(2.0)
        else:
            # Flujo Exitoso
            cola_mensajes.put("Puerta abierta")
            registrar_acceso(usuario) 
            time.sleep(2.0)
        
        cola_mensajes.put("TERMINADO")

def monitor_sistema_thread():
    """Hilo de monitoreo en segundo plano (Watchdog)."""
    while True:
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM accesos")
            total_logs = cursor.fetchone()[0]
            conn.close()
            print(f"[MONITOR] Base de datos activa. Registros válidos actuales: {total_logs}")
        except sqlite3.Error as e:
            print(f"[MONITOR] Error: {e}")
            
        time.sleep(10)