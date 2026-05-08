from datetime import datetime

def registrar_acceso(usuario):
    """Guarda la fecha, hora y el usuario que abrió la puerta."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{timestamp}] ACCESO: El usuario '{usuario}' ha abierto la puerta.\n"
    
    try:
        with open("log_accesos.txt", "a", encoding="utf-8") as archivo:
            archivo.write(linea)
    except Exception as e:
        print(f"Error al escribir en el registro: {e}")