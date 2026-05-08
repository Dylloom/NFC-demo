import tkinter as tk
from tkinter import messagebox
import threading
from auth import verificar_credenciales
from hardware import simulacion_nfc_thread
from config import cola_mensajes, TITULO_APP

class InterfazNFC:
    def __init__(self, root):
        self.root = root
        self.root.title(TITULO_APP)
        self.root.geometry("350x450")
        
        # Variable para identificar quién está operando el sistema
        self.usuario_actual = None
        
        # Contenedor dinámico
        self.contenedor = tk.Frame(self.root)
        self.contenedor.pack(expand=True, fill="both")
        
        # Iniciar en la pantalla de login
        self.pantalla_login()

    def limpiar_pantalla(self):
        """Elimina todos los widgets del contenedor para cambiar de vista."""
        for widget in self.contenedor.winfo_children():
            widget.destroy()

    # --- VISTA 1: LOGIN ---
    def pantalla_login(self):
        self.limpiar_pantalla()
        
        tk.Label(self.contenedor, text="SEGURIDAD NFC", font=("Arial", 16, "bold"), fg="#2C3E50").pack(pady=30)
        
        tk.Label(self.contenedor, text="Usuario:", font=("Arial", 10)).pack()
        self.entry_user = tk.Entry(self.contenedor, font=("Arial", 11), justify="center")
        self.entry_user.pack(pady=5)
        
        tk.Label(self.contenedor, text="Contraseña:", font=("Arial", 10)).pack()
        self.entry_pass = tk.Entry(self.contenedor, show="*", font=("Arial", 11), justify="center")
        self.entry_pass.pack(pady=5)
        
        tk.Button(
            self.contenedor, 
            text="INGRESAR", 
            command=self.intentar_login,
            bg="#2C3E50", fg="white", 
            font=("Arial", 10, "bold"),
            width=15, pady=8
        ).pack(pady=30)

    def intentar_login(self):
        user = self.entry_user.get()
        password = self.entry_pass.get()
        
        if verificar_credenciales(user, password):
            self.usuario_actual = user  # Guardamos el usuario que inició sesión
            self.pantalla_puerta()
        else:
            messagebox.showerror("Error de Acceso", "Usuario o contraseña incorrectos.")

    # --- VISTA 2: BOTÓN DE APERTURA ---
    def pantalla_puerta(self):
        self.limpiar_pantalla()
        
        tk.Label(
            self.contenedor, 
            text=f"Bienvenido, {self.usuario_actual}", 
            font=("Arial", 10, "italic")
        ).pack(pady=10)

        self.label_estado = tk.Label(
            self.contenedor, 
            text="Listo para abrir", 
            font=("Arial", 12, "bold"), 
            fg="#7F8C8D"
        )
        self.label_estado.pack(pady=40)
        
        # Botón central de apertura
        self.btn_abrir = tk.Button(
            self.contenedor, 
            text="ABRIR PUERTA", 
            command=self.ejecutar_proceso_nfc,
            font=("Arial", 12, "bold"), 
            bg="#27AE60", fg="white",
            width=20, height=4,
            relief="raised"
        )
        self.btn_abrir.pack(expand=True)

    # --- LÓGICA DE CONTROL ---
    def ejecutar_proceso_nfc(self):
        """Inicia el hilo de hardware y la escucha de la cola."""
        # Deshabilitar interfaz mientras se procesa
        self.btn_abrir.config(state="disabled", bg="#BDC3C7")
        
        # Creamos el hilo del hardware pasando el usuario actual para el .txt
        hilo_hardware = threading.Thread(
            target=simulacion_nfc_thread, 
            args=(self.usuario_actual,)
        )
        hilo_hardware.start()
        
        # Empezar a monitorear la cola de mensajes para actualizar la pantalla
        self.escuchar_cola()

    def escuchar_cola(self):
        """Revisa la cola de mensajes provenientes del hilo de hardware."""
        try:
            # Intentamos obtener un mensaje sin bloquear el hilo principal de la GUI
            mensaje = cola_mensajes.get_nowait()
            
            if mensaje == "TERMINADO":
                # Restaurar el botón y el estado
                self.label_estado.config(text="Listo para abrir", fg="#7F8C8D")
                self.btn_abrir.config(state="normal", bg="#27AE60")
                return # Salimos del ciclo de escucha
            
            # Si hay un mensaje de estado, lo mostramos
            self.label_estado.config(text=mensaje, fg="#2980B9")
            
            # Volver a revisar en 100 milisegundos
            self.root.after(100, self.escuchar_cola)
            
        except:
            # Si la cola está vacía, seguimos esperando el siguiente paso
            self.root.after(100, self.escuchar_cola)
