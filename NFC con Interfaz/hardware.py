import time
from config import semaforo_nfc, cola_mensajes
from registro import registrar_acceso  # Importamos el nuevo módulo

def simulacion_nfc_thread(usuario):
    """Recibe el usuario para poder registrarlo en el .txt"""
    with semaforo_nfc:
        cola_mensajes.put("Acercar a la puerta")
        time.sleep(1.5)
        
        cola_mensajes.put("Leyendo NFC...")
        time.sleep(1.5)
        
        # Momento clave: Se abre la puerta y se registra
        cola_mensajes.put("Puerta abierta")
        registrar_acceso(usuario) 
        time.sleep(2.0)
        
        cola_mensajes.put("TERMINADO")