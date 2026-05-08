import tkinter as tk
from gui import InterfazNFC

if __name__ == "__main__":
    # Creamos la ventana principal
    root = tk.Tk()
    
    # Instanciamos nuestra interfaz (que está en el otro archivo)
    app = InterfazNFC(root)
    
    # Iniciamos el bucle de la aplicación
    root.mainloop()