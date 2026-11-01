import tkinter as tk
from tkinter import ttk, messagebox
import threading
from auth import verificar_credenciales
from hardware import simulacion_nfc_thread
from database import (
    obtener_registros_acceso, obtener_todo_db, registrar_usuario, 
    obtener_rol, bloquear_usuario_db, desbloquear_usuario_db, 
    obtener_bloqueados_db, es_bloqueado_db, obtener_todos_los_usuarios
)
from config import cola_mensajes, TITULO_APP, HOST_CHAT, PORT_CHAT
from chat_client import ClienteChat

COLOR_BG = "#1E1E2E"
COLOR_CARD = "#252538"
COLOR_TEXT = "#CDD6F4"
COLOR_SUBTEXT = "#A6ADC8"
COLOR_INPUT = "#11111B"
COLOR_GREEN = "#A6E3A1"
COLOR_RED = "#F38BA8"
COLOR_PURPLE = "#CBA6F7"
COLOR_BLUE = "#89B4FA"

class BotonRedondeado(tk.Canvas):
    def __init__(self, parent, text, command, bg, fg, width, height, radius=18, font=("Arial", 10, "bold")):
        self.w = width
        self.h = height
        super().__init__(parent, width=self.w, height=self.h, bg=parent["bg"], highlightthickness=0, cursor="hand2")
        self.command = command
        self.bg = bg
        self.fg = fg
        self.radius = radius
        self.text_str = text
        self.font = font
        self.estado = "normal"
        self.dibujar()

    def dibujar(self):
        self.delete("all")
        r = self.radius
        points = [r, 0, r, 0, self.w-r, 0, self.w-r, 0, self.w, 0, self.w, r, self.w, r, self.w, self.h-r, self.w, self.h-r, self.w, self.h, self.w-r, self.h, self.w-r, self.h, r, self.h, r, self.h, 0, self.h, 0, self.h-r, 0, self.h-r, 0, r, 0, r, 0, 0]
        self.rect_id = self.create_polygon(points, fill=self.bg, smooth=True)
        self.text_id = self.create_text(self.w // 2, self.h // 2, text=self.text_str, fill=self.fg, font=self.font)
        
        if self.estado == "normal":
            self.tag_bind(self.rect_id, "<Button-1>", lambda e: self.command())
            self.tag_bind(self.text_id, "<Button-1>", lambda e: self.command())

    def configurar_estado(self, nuevo_estado, nuevo_bg=None):
        self.estado = nuevo_estado
        if nuevo_estado == "disabled":
            self.bg = "#45475A"
        else:
            self.bg = nuevo_bg or "#27AE60"
        self.dibujar()


class InterfazNFC:
    def __init__(self, root):
        self.root = root
        self.root.title(TITULO_APP)
        self.root.geometry("420x680")
        self.root.configure(bg=COLOR_BG)
        
        self.usuario_actual = None
        self.contenedor = tk.Frame(self.root, bg=COLOR_BG)
        self.contenedor.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.pantalla_login()

    def limpiar_pantalla(self):
        for widget in self.contenedor.winfo_children():
            widget.destroy()

    def pantalla_login(self):
        self.limpiar_pantalla()
        card = tk.Frame(self.contenedor, bg=COLOR_CARD)
        card.pack(expand=True, fill="both", padx=10, pady=10)

        tk.Label(card, text="🛡️", font=("Arial", 36), bg=COLOR_CARD).pack(pady=(20, 5))
        tk.Label(card, text="CONTROL DE ACCESO", font=("Arial", 14, "bold"), fg=COLOR_TEXT, bg=COLOR_CARD).pack()
        tk.Label(card, text="Por favor, identifíquese", font=("Arial", 9), fg=COLOR_SUBTEXT, bg=COLOR_CARD).pack(pady=(0, 20))
        
        tk.Label(card, text="Usuario", font=("Arial", 10, "bold"), fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=30)
        self.entry_user = tk.Entry(card, font=("Arial", 11), justify="center", bd=0, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT)
        self.entry_user.pack(fill="x", padx=30, pady=(5, 15), ipady=6)
        
        tk.Label(card, text="Contraseña", font=("Arial", 10, "bold"), fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=30)
        self.entry_pass = tk.Entry(card, show="*", font=("Arial", 11), justify="center", bd=0, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT)
        self.entry_pass.pack(fill="x", padx=30, pady=(5, 20), ipady=6)
        
        btn_ingresar = BotonRedondeado(card, text="INGRESAR", command=self.intentar_login, bg=COLOR_GREEN, fg=COLOR_INPUT, width=220, height=40)
        btn_ingresar.pack(pady=5)

        btn_ir_registro = BotonRedondeado(card, text="CREAR CUENTA NUEVA", command=self.pantalla_registro, bg=COLOR_BLUE, fg=COLOR_INPUT, width=220, height=35)
        btn_ir_registro.pack(pady=10)

    def intentar_login(self):
        user = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()
        
        if verificar_credenciales(user, password):
            self.usuario_actual = user
            self.pantalla_puerta()
        else:
            messagebox.showerror("Error", "Credenciales incorrectas.")

    def pantalla_registro(self):
        self.limpiar_pantalla()
        card = tk.Frame(self.contenedor, bg=COLOR_CARD)
        card.pack(expand=True, fill="both", padx=10, pady=10)

        tk.Label(card, text="📝", font=("Arial", 36), bg=COLOR_CARD).pack(pady=(20, 5))
        tk.Label(card, text="NUEVO REGISTRO", font=("Arial", 14, "bold"), fg=COLOR_TEXT, bg=COLOR_CARD).pack()

        tk.Label(card, text="Elige un Usuario", font=("Arial", 10, "bold"), fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=30)
        self.reg_user = tk.Entry(card, font=("Arial", 11), justify="center", bd=0, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT)
        self.reg_user.pack(fill="x", padx=30, pady=(5, 15), ipady=6)
        
        tk.Label(card, text="Elige una Contraseña", font=("Arial", 10, "bold"), fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=30)
        self.reg_pass = tk.Entry(card, show="*", font=("Arial", 11), justify="center", bd=0, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT)
        self.reg_pass.pack(fill="x", padx=30, pady=(5, 25), ipady=6)

        btn_confirmar = BotonRedondeado(card, text="REGISTRARSE", command=self.intentar_registro, bg=COLOR_GREEN, fg=COLOR_INPUT, width=220, height=40)
        btn_confirmar.pack(pady=5)

        btn_volver = BotonRedondeado(card, text="VOLVER AL LOGIN", command=self.pantalla_login, bg=COLOR_SUBTEXT, fg=COLOR_INPUT, width=220, height=35)
        btn_volver.pack(pady=10)

    def intentar_registro(self):
        nuevo_usuario = self.reg_user.get().strip()
        nueva_pass = self.reg_pass.get().strip()

        if not nuevo_usuario or not nueva_pass:
            messagebox.showwarning("Campos Vacíos", "Por favor completa todos los datos.")
            return

        if registrar_usuario(nuevo_usuario, nueva_pass):
            messagebox.showinfo("Éxito", f"¡Usuario '{nuevo_usuario}' registrado!")
            self.pantalla_login()
        else:
            messagebox.showerror("Error", "El usuario ya existe.")

    def pantalla_puerta(self):
        self.limpiar_pantalla()
        card = tk.Frame(self.contenedor, bg=COLOR_CARD)
        card.pack(expand=True, fill="both", padx=10, pady=10)

        rol_actual = obtener_rol(self.usuario_actual)
        tk.Label(card, text=f"Usuario activo: {self.usuario_actual} ({rol_actual.upper()})", font=("Arial", 9, "italic"), fg=COLOR_SUBTEXT, bg=COLOR_CARD).pack(pady=10)

        self.label_estado = tk.Label(card, text="Listo para operar", font=("Arial", 12, "bold"), fg=COLOR_SUBTEXT, bg=COLOR_CARD)
        self.label_estado.pack(pady=(10, 5))
        
        self.btn_abrir = BotonRedondeado(card, text="ABRIR PUERTA", command=lambda: self.ejecutar_proceso_nfc(False), bg=COLOR_GREEN, fg=COLOR_INPUT, width=240, height=40)
        self.btn_abrir.pack(pady=5)

        self.btn_fallar = BotonRedondeado(card, text="SIMULAR FALLO NFC", command=lambda: self.ejecutar_proceso_nfc(True), bg=COLOR_RED, fg=COLOR_INPUT, width=240, height=40)
        self.btn_fallar.pack(pady=5)

        # Botón Acceso al Chat
        self.btn_chat = BotonRedondeado(card, text="💬 CHAT Y CONSULTAS", command=self.abrir_ventana_chat, bg=COLOR_BLUE, fg=COLOR_INPUT, width=240, height=40)
        self.btn_chat.pack(pady=8)

        # Botón Lista Negra Personal
        self.btn_blacklist = BotonRedondeado(card, text="🚫 MI LISTA NEGRA", command=self.abrir_ventana_lista_negra_personal, bg=COLOR_PURPLE, fg=COLOR_INPUT, width=240, height=35)
        self.btn_blacklist.pack(pady=5)

    def ejecutar_proceso_nfc(self, forzar_fallo):
        self.btn_abrir.configurar_estado("disabled")
        self.btn_fallar.configurar_estado("disabled")
        hilo_hardware = threading.Thread(target=simulacion_nfc_thread, args=(self.usuario_actual, forzar_fallo))
        hilo_hardware.start()
        self.escuchar_cola()

    def escuchar_cola(self):
        try:
            mensaje = cola_mensajes.get_nowait()
            if mensaje == "TERMINADO":
                self.label_estado.config(text="Listo para operar", fg=COLOR_SUBTEXT)
                self.btn_abrir.configurar_estado("normal", COLOR_GREEN)
                self.btn_fallar.configurar_estado("normal", COLOR_RED)
                return
            
            if "ERROR" in mensaje:
                self.label_estado.config(text=mensaje, fg=COLOR_RED)
            else:
                self.label_estado.config(text=mensaje, fg=COLOR_GREEN)
                
            self.root.after(100, self.escuchar_cola)
        except:
            self.root.after(100, self.escuchar_cola)

    # --- VENTANA DE CHAT INTEGRADO (GENERAL Y 1 A 1) ---
    def abrir_ventana_chat(self):
        v_chat = tk.Toplevel(self.root)
        v_chat.title(f"Centro de Mensajes - {self.usuario_actual}")
        v_chat.geometry("500x560")
        v_chat.configure(bg=COLOR_BG)

        notebook = ttk.Notebook(v_chat)
        notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # Tab 1: Chat General
        tab_general = tk.Frame(notebook, bg=COLOR_BG)
        notebook.add(tab_general, text="📢 Chat General (Todos)")

        # Tab 2: Chat 1 a 1
        tab_privado = tk.Frame(notebook, bg=COLOR_BG)
        notebook.add(tab_privado, text="👤 Chat 1 a 1 (Privado)")

        # --- Pestaña 1: Componentes Chat General ---
        txt_gen = tk.Text(tab_general, bg=COLOR_INPUT, fg=COLOR_TEXT, bd=0, font=("Consolas", 9), state="disabled")
        txt_gen.pack(expand=True, fill="both", padx=10, pady=10)

        frame_gen_input = tk.Frame(tab_general, bg=COLOR_BG)
        frame_gen_input.pack(fill="x", padx=10, pady=5)
        entry_gen = tk.Entry(frame_gen_input, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT, font=("Arial", 10))
        entry_gen.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 5))

        # --- Pestaña 2: Componentes Chat 1 a 1 ---
        frame_top_p = tk.Frame(tab_privado, bg=COLOR_BG)
        frame_top_p.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_top_p, text="Destinatario:", fg=COLOR_TEXT, bg=COLOR_BG, font=("Arial", 9, "bold")).pack(side="left")
        
        usuarios_disp = [u for u in obtener_todos_los_usuarios() if u != self.usuario_actual]
        combo_dest = ttk.Combobox(frame_top_p, values=usuarios_disp, state="readonly", width=15)
        if usuarios_disp:
            combo_dest.current(0)
        combo_dest.pack(side="left", padx=5)

        txt_priv = tk.Text(tab_privado, bg=COLOR_INPUT, fg=COLOR_TEXT, bd=0, font=("Consolas", 9), state="disabled")
        txt_priv.pack(expand=True, fill="both", padx=10, pady=5)

        frame_priv_input = tk.Frame(tab_privado, bg=COLOR_BG)
        frame_priv_input.pack(fill="x", padx=10, pady=5)
        entry_priv = tk.Entry(frame_priv_input, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT, font=("Arial", 10))
        entry_priv.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 5))

        # FILTRADO DE LISTA NEGRA PERSONAL EN TIEMPO REAL
        def recibir_mensaje_servidor(raw):
            partes = raw.split("|", 2)
            header = partes[0]

            if header == "SYSTEM":
                msg = partes[1]
                _append_text(txt_gen, f"[SISTEMA] {msg}")
                _append_text(txt_priv, f"[SISTEMA] {msg}")

            elif header == "GLOBAL":
                remitente = partes[1]
                contenido = partes[2]
                # Si el remitente está en la Lista Negra Personal de este usuario, SE IGNORA
                if es_bloqueado_db(self.usuario_actual, remitente):
                    return
                _append_text(txt_gen, f"{remitente}: {contenido}")

            elif header == "PRIVATE":
                remitente = partes[1]
                contenido = partes[2]
                # Si el remitente está bloqueado personalmente, SE IGNORA
                if es_bloqueado_db(self.usuario_actual, remitente):
                    return
                _append_text(txt_priv, f"[{remitente} -> Mí]: {contenido}")

        def _append_text(widget_txt, linea):
            widget_txt.config(state="normal")
            widget_txt.insert("end", linea + "\n")
            widget_txt.see("end")
            widget_txt.config(state="disabled")

        cliente = ClienteChat(HOST_CHAT, PORT_CHAT, self.usuario_actual, recibir_mensaje_servidor)
        ok, error = cliente.conectar()
        if not ok:
            messagebox.showerror("Error", f"No se pudo conectar al servidor de chat:\n{error}")
            v_chat.destroy()
            return

        def enviar_gen():
            t = entry_gen.get().strip()
            if t:
                cliente.enviar_global(t)
                entry_gen.delete(0, "end")

        def enviar_priv():
            dest = combo_dest.get().strip()
            t = entry_priv.get().strip()
            if not dest:
                messagebox.showwarning("Atención", "Selecciona un usuario destinatario.")
                return
            if t:
                cliente.enviar_privado(dest, t)
                entry_priv.delete(0, "end")

        btn_send_gen = BotonRedondeado(frame_gen_input, text="ENVIAR", command=enviar_gen, bg=COLOR_GREEN, fg=COLOR_INPUT, width=80, height=30)
        btn_send_gen.pack(side="right")

        btn_send_priv = BotonRedondeado(frame_priv_input, text="ENVIAR 1a1", command=enviar_priv, bg=COLOR_BLUE, fg=COLOR_INPUT, width=90, height=30)
        btn_send_priv.pack(side="right")

        def al_cerrar():
            cliente.desconectar()
            v_chat.destroy()

        v_chat.protocol("WM_DELETE_WINDOW", al_cerrar)

    # --- VENTANA: LISTA NEGRA PERSONAL DE CADA USUARIO ---
    def abrir_ventana_lista_negra_personal(self):
        v_bl = tk.Toplevel(self.root)
        v_bl.title("Mi Lista Negra Personal")
        v_bl.geometry("380x420")
        v_bl.configure(bg=COLOR_BG)

        tk.Label(v_bl, text="MI LISTA NEGRA DE CONTACTOS", font=("Arial", 11, "bold"), fg=COLOR_PURPLE, bg=COLOR_BG).pack(pady=10)
        tk.Label(v_bl, text="Los mensajes de usuarios bloqueados no aparecerán en tu chat", font=("Arial", 8), fg=COLOR_SUBTEXT, bg=COLOR_BG).pack()

        lista_box = tk.Listbox(v_bl, bg=COLOR_INPUT, fg=COLOR_RED, bd=0, font=("Consolas", 10))
        lista_box.pack(expand=True, fill="both", padx=20, pady=10)

        def actualizar_lista():
            lista_box.delete(0, "end")
            bloqueados = obtener_bloqueados_db(self.usuario_actual)
            for b in bloqueados:
                lista_box.insert("end", f" 🚫 {b}")

        actualizar_lista()

        frame_add = tk.Frame(v_bl, bg=COLOR_BG)
        frame_add.pack(fill="x", padx=20, pady=5)

        todos_usrs = [u for u in obtener_todos_los_usuarios() if u != self.usuario_actual]
        combo_block = ttk.Combobox(frame_add, values=todos_usrs, state="readonly", width=12)
        if todos_usrs:
            combo_block.current(0)
        combo_block.pack(side="left", padx=5)

        def bloquear_sel():
            target = combo_block.get().strip()
            if target:
                if bloquear_usuario_db(self.usuario_actual, target):
                    messagebox.showinfo("Éxito", f"Usuario '{target}' agregado a tu lista negra.")
                    actualizar_lista()

        def desbloquear_sel():
            sel = lista_box.curselection()
            if not sel:
                messagebox.showwarning("Atención", "Selecciona un usuario de la lista.")
                return
            linea = lista_box.get(sel[0])
            usr_target = linea.replace(" 🚫 ", "").strip()
            if desbloquear_usuario_db(self.usuario_actual, usr_target):
                messagebox.showinfo("Éxito", f"Usuario '{usr_target}' desbloqueado.")
                actualizar_lista()

        btn_add = BotonRedondeado(frame_add, text="BLOQUEAR", command=bloquear_sel, bg=COLOR_RED, fg=COLOR_INPUT, width=90, height=30)
        btn_add.pack(side="left", padx=5)

        btn_del = BotonRedondeado(v_bl, text="DESBLOQUEAR SELECCIONADO", command=desbloquear_sel, bg=COLOR_GREEN, fg=COLOR_INPUT, width=220, height=35)
        btn_del.pack(pady=10)
