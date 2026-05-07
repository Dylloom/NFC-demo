from lector import LectorNFC
from dispositivo import PersonaConNFC
import time

def ejecutar_simulacion():
    print("=== SIMULACIÓN DE ACCESO NFC SECUENCIAL ===\n")

    # 1. Encendemos el lector (hilo secundario/daemon)
    lector = LectorNFC()
    lector.start()

    # 2. Definimos a las personas que van a pasar
    cola_de_personas = [
        PersonaConNFC("Carlos", "99A1"),
        PersonaConNFC("Desconocido", "XXXX"),
        PersonaConNFC("Ana", "44B2")
    ]

    # 3. Hacemos que pasen uno por uno
    for persona in cola_de_personas:
        persona.start()
        # Esperamos a que la persona termine su proceso antes de lanzar la siguiente
        # Esto garantiza el orden "uno a la vez" en la consola
        persona.join() 
        time.sleep(1) # Pausa entre personas para realismo

    print("=== Fin de la jornada. Todos los intentos procesados. ===")

if __name__ == "__main__":
    ejecutar_simulacion()
