import tkinter as tk
import threading
from gui import InterfazNFC
from database import inicializar_base_datos
from hardware import monitor_sistema_thread
from chat_server import servidor_chat_instancia

if __name__ == "__main__":
    # 1. Inicializar la Base de Datos SQLite y Tablas Relacionales
    inicializar_base_datos()
    
    # 2. Iniciar el Servidor de Chat TCP Multihilo en un hilo secundario Daemon
    hilo_servidor_chat = threading.Thread(target=servidor_chat_instancia.iniciar, daemon=True)
    hilo_servidor_chat.start()

    # 3. Iniciar el Hilo de Monitorización de Fondo
    hilo_auditor = threading.Thread(target=monitor_sistema_thread, daemon=True)
    hilo_auditor.start()
    
    # 4. Lanzar la Interfaz Gráfica Tkinter
    root = tk.Tk()
    app = InterfazNFC(root)
    root.mainloop()
