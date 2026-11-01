import tkinter as tk
from tkinter import ttk, messagebox
import threading
from auth import verificar_credenciales
from hardware import simulacion_nfc_thread
from database import (
    obtener_registros_acceso, obtener_todo_db, registrar_usuario, 
    obtener_rol, cambiar_rol_usuario, eliminar_usuario_db,
    bloquear_usuario_db, desbloquear_usuario_db, 
    obtener_bloqueados_db, es_bloqueado_db, obtener_todos_los_usuarios
)
from config import cola_mensajes, TITULO_APP, HOST_CHAT, PORT_CHAT
from chat_client import ClienteChat

# ==========================================
# PALETA DE COLORES (Dark Dashboard Premium)
# ==========================================
COLOR_BG = "#11111B"          # Fondo principal ultrasuave
COLOR_CARD = "#1E1E2E"        # Tarjetas contenedoras
COLOR_CARD_BORDER = "#313244" # Bordes de división
COLOR_INPUT = "#313244"       # Campos de entrada / Cajas de texto
COLOR_TEXT = "#CDD6F4"        # Texto principal
COLOR_SUBTEXT = "#A6ADC8"     # Subtítulos y aclaraciones
COLOR_GREEN = "#A6E3A1"       # Éxito / Apertura
COLOR_GREEN_HOVER = "#89DCEB"
COLOR_RED = "#F38BA8"         # Alertas / Fallos
COLOR_RED_HOVER = "#EBA0AC"
COLOR_PURPLE = "#CBA6F7"      # Módulos especiales / Admin
COLOR_PURPLE_HOVER = "#B4BEFE"
COLOR_BLUE = "#89B4FA"        # Acciones secundarias / Chat
COLOR_BLUE_HOVER = "#74C7EC"

FONT_MAIN = "Segoe UI"

# ==========================================
# BOTÓN REDONDEADO CON EFECTO HOVER
# ==========================================
class BotonRedondeado(tk.Canvas):
    def __init__(self, parent, text, command, bg, fg, width, height, radius=14, font=(FONT_MAIN, 9, "bold"), hover_bg=None):
        self.w = width
        self.h = height
        super().__init__(parent, width=self.w, height=self.h, bg=parent["bg"], highlightthickness=0, cursor="hand2")
        self.command = command
        self.bg = bg
        self.hover_bg = hover_bg or bg
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
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        if self.estado == "normal":
            self.itemconfig(self.rect_id, fill=self.hover_bg)

    def _on_leave(self, e):
        if self.estado == "normal":
            self.itemconfig(self.rect_id, fill=self.bg)

    def configurar_estado(self, nuevo_estado, nuevo_bg=None):
        self.estado = nuevo_estado
        if nuevo_estado == "disabled":
            self.bg = "#45475A"
            self.hover_bg = "#45475A"
        else:
            self.bg = nuevo_bg or self.bg
            self.hover_bg = self.bg
        self.dibujar()


# ==========================================
# CLASE PRINCIPAL GUI (DASHBOARD)
# ==========================================
class InterfazNFC:
    def __init__(self, root):
        self.root = root
        self.root.title(TITULO_APP)
        self.root.geometry("480x680")
        self.root.configure(bg=COLOR_BG)
        
        self.aplicar_estilos_ttk()
        self.usuario_actual = None
        
        self.contenedor = tk.Frame(self.root, bg=COLOR_BG)
        self.contenedor.pack(expand=True, fill="both", padx=15, pady=15)
        
        self.pantalla_login()

    def aplicar_estilos_ttk(self):
        """Aplica estilos oscuros unificados para los controles nativos de Tkinter (Tabs/Combobox)."""
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TNotebook", background=COLOR_BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=COLOR_CARD, foreground=COLOR_SUBTEXT, padding=[12, 6], font=(FONT_MAIN, 9, "bold"), borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", COLOR_BLUE)], foreground=[("selected", COLOR_INPUT)])
        style.configure("TCombobox", fieldbackground=COLOR_INPUT, background=COLOR_CARD, foreground=COLOR_TEXT, arrowcolor=COLOR_TEXT, borderwidth=0)
        style.map("TCombobox", fieldbackground=[("readonly", COLOR_INPUT)], foreground=[("readonly", COLOR_TEXT)])

    def limpiar_pantalla(self):
        for widget in self.contenedor.winfo_children():
            widget.destroy()

    # --- PANTALLA 1: LOGIN ---
    def pantalla_login(self):
        self.limpiar_pantalla()
        card = tk.Frame(self.contenedor, bg=COLOR_CARD, highlightbackground=COLOR_CARD_BORDER, highlightthickness=1)
        card.pack(expand=True, fill="both", padx=20, pady=20)

        tk.Label(card, text="🛡️", font=(FONT_MAIN, 42), bg=COLOR_CARD).pack(pady=(25, 5))
        tk.Label(card, text="CONTROL DE ACCESO", font=(FONT_MAIN, 14, "bold"), fg=COLOR_TEXT, bg=COLOR_CARD).pack()
        tk.Label(card, text="Ingrese sus credenciales para continuar", font=(FONT_MAIN, 8), fg=COLOR_SUBTEXT, bg=COLOR_CARD).pack(pady=(2, 20))
        
        tk.Label(card, text="Usuario", font=(FONT_MAIN, 9, "bold"), fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=30)
        self.entry_user = tk.Entry(card, font=(FONT_MAIN, 10), justify="center", bd=0, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT)
        self.entry_user.pack(fill="x", padx=30, pady=(5, 15), ipady=7)
        
        tk.Label(card, text="Contraseña", font=(FONT_MAIN, 9, "bold"), fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=30)
        self.entry_pass = tk.Entry(card, show="*", font=(FONT_MAIN, 10), justify="center", bd=0, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT)
        self.entry_pass.pack(fill="x", padx=30, pady=(5, 20), ipady=7)
        
        btn_ingresar = BotonRedondeado(card, text="INICIAR SESIÓN", command=self.intentar_login, bg=COLOR_GREEN, hover_bg=COLOR_GREEN_HOVER, fg=COLOR_INPUT, width=230, height=40)
        btn_ingresar.pack(pady=5)

        btn_ir_registro = BotonRedondeado(card, text="CREAR CUENTA NUEVA", command=self.pantalla_registro, bg=COLOR_BLUE, hover_bg=COLOR_BLUE_HOVER, fg=COLOR_INPUT, width=230, height=35)
        btn_ir_registro.pack(pady=10)

    def intentar_login(self):
        user = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()
        
        if verificar_credenciales(user, password):
            self.usuario_actual = user
            self.pantalla_puerta()
        else:
            messagebox.showerror("Error", "Credenciales incorrectas.")

    # --- PANTALLA 2: REGISTRO ---
    def pantalla_registro(self):
        self.limpiar_pantalla()
        card = tk.Frame(self.contenedor, bg=COLOR_CARD, highlightbackground=COLOR_CARD_BORDER, highlightthickness=1)
        card.pack(expand=True, fill="both", padx=20, pady=20)

        tk.Label(card, text="📝", font=(FONT_MAIN, 42), bg=COLOR_CARD).pack(pady=(25, 5))
        tk.Label(card, text="NUEVO REGISTRO", font=(FONT_MAIN, 14, "bold"), fg=COLOR_TEXT, bg=COLOR_CARD).pack()

        tk.Label(card, text="Nombre de Usuario", font=(FONT_MAIN, 9, "bold"), fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=30, pady=(15, 0))
        self.reg_user = tk.Entry(card, font=(FONT_MAIN, 10), justify="center", bd=0, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT)
        self.reg_user.pack(fill="x", padx=30, pady=(5, 15), ipady=7)
        
        tk.Label(card, text="Contraseña", font=(FONT_MAIN, 9, "bold"), fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=30)
        self.reg_pass = tk.Entry(card, show="*", font=(FONT_MAIN, 10), justify="center", bd=0, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT)
        self.reg_pass.pack(fill="x", padx=30, pady=(5, 25), ipady=7)

        btn_confirmar = BotonRedondeado(card, text="REGISTRARSE", command=self.intentar_registro, bg=COLOR_GREEN, hover_bg=COLOR_GREEN_HOVER, fg=COLOR_INPUT, width=230, height=40)
        btn_confirmar.pack(pady=5)

        btn_volver = BotonRedondeado(card, text="VOLVER AL LOGIN", command=self.pantalla_login, bg=COLOR_SUBTEXT, fg=COLOR_INPUT, width=230, height=35)
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

    # --- PANTALLA 3: DASHBOARD PRINCIPAL ---
    def pantalla_puerta(self):
        self.limpiar_pantalla()
        rol_actual = obtener_rol(self.usuario_actual)

        # -------------------------------------------------------------
        # HEADER BAR: Perfil de usuario + Botón Salir
        # -------------------------------------------------------------
        top_bar = tk.Frame(self.contenedor, bg=COLOR_CARD, highlightbackground=COLOR_CARD_BORDER, highlightthickness=1)
        top_bar.pack(fill="x", pady=(0, 12), ipady=3)

        user_info = tk.Frame(top_bar, bg=COLOR_CARD)
        user_info.pack(side="left", padx=12)
        tk.Label(user_info, text="👤", font=(FONT_MAIN, 11), bg=COLOR_CARD, fg=COLOR_BLUE).pack(side="left", padx=(0, 4))
        tk.Label(user_info, text=self.usuario_actual, font=(FONT_MAIN, 10, "bold"), fg=COLOR_TEXT, bg=COLOR_CARD).pack(side="left")
        
        badge_bg = COLOR_PURPLE if rol_actual == "admin" else COLOR_BLUE
        role_badge = tk.Label(top_bar, text=f" {rol_actual.upper()} ", font=(FONT_MAIN, 8, "bold"), fg=COLOR_INPUT, bg=badge_bg)
        role_badge.pack(side="left", padx=8)

        btn_logout = BotonRedondeado(top_bar, text="SALIR", command=self.pantalla_login, bg=COLOR_INPUT, hover_bg=COLOR_CARD_BORDER, fg=COLOR_RED, width=65, height=28, radius=10, font=(FONT_MAIN, 8, "bold"))
        btn_logout.pack(side="right", padx=10)

        # -------------------------------------------------------------
        # TARJETA 1: CONTROL DE ACCESO FÍSICO
        # -------------------------------------------------------------
        card_puerta = tk.Frame(self.contenedor, bg=COLOR_CARD, highlightbackground=COLOR_CARD_BORDER, highlightthickness=1)
        card_puerta.pack(fill="x", pady=(0, 12), ipadx=10, ipady=10)

        tk.Label(card_puerta, text="🚪  CONTROL DE ACCESO FÍSICO", font=(FONT_MAIN, 9, "bold"), fg=COLOR_SUBTEXT, bg=COLOR_CARD).pack(anchor="w", padx=15, pady=(5, 8))

        # Indicador de estado
        self.frame_estado = tk.Frame(card_puerta, bg=COLOR_INPUT, padx=10, pady=6)
        self.frame_estado.pack(fill="x", padx=15, pady=(0, 10))
        self.label_estado = tk.Label(self.frame_estado, text="🟢  SISTEMA LISTO", font=(FONT_MAIN, 10, "bold"), fg=COLOR_GREEN, bg=COLOR_INPUT)
        self.label_estado.pack()

        # Botones en 2 columnas (paralelos)
        grid_puerta = tk.Frame(card_puerta, bg=COLOR_CARD)
        grid_puerta.pack(fill="x", padx=15)

        self.btn_abrir = BotonRedondeado(grid_puerta, text="🔓 ABRIR PUERTA", command=lambda: self.ejecutar_proceso_nfc(False), bg=COLOR_GREEN, hover_bg=COLOR_GREEN_HOVER, fg=COLOR_INPUT, width=198, height=38)
        self.btn_abrir.pack(side="left", expand=True, padx=(0, 4))

        self.btn_fallar = BotonRedondeado(grid_puerta, text="⚠️ FALLO NFC", command=lambda: self.ejecutar_proceso_nfc(True), bg=COLOR_RED, hover_bg=COLOR_RED_HOVER, fg=COLOR_INPUT, width=198, height=38)
        self.btn_fallar.pack(side="right", expand=True, padx=(4, 0))

        # -------------------------------------------------------------
        # TARJETA 2: SERVICIOS Y COMUNICACIÓN
        # -------------------------------------------------------------
        card_servicios = tk.Frame(self.contenedor, bg=COLOR_CARD, highlightbackground=COLOR_CARD_BORDER, highlightthickness=1)
        card_servicios.pack(fill="x", pady=(0, 12), ipadx=10, ipady=10)

        tk.Label(card_servicios, text="💬  COMUNICACIÓN Y PRIVACIDAD", font=(FONT_MAIN, 9, "bold"), fg=COLOR_SUBTEXT, bg=COLOR_CARD).pack(anchor="w", padx=15, pady=(5, 8))

        grid_servicios = tk.Frame(card_servicios, bg=COLOR_CARD)
        grid_servicios.pack(fill="x", padx=15)

        self.btn_chat = BotonRedondeado(grid_servicios, text="💬 CHAT EN VIVO", command=self.abrir_ventana_chat, bg=COLOR_BLUE, hover_bg=COLOR_BLUE_HOVER, fg=COLOR_INPUT, width=198, height=38)
        self.btn_chat.pack(side="left", expand=True, padx=(0, 4))

        self.btn_blacklist = BotonRedondeado(grid_servicios, text="🚫 LISTA NEGRA", command=self.abrir_ventana_lista_negra_personal, bg=COLOR_PURPLE, hover_bg=COLOR_PURPLE_HOVER, fg=COLOR_INPUT, width=198, height=38)
        self.btn_blacklist.pack(side="right", expand=True, padx=(4, 0))

        # -------------------------------------------------------------
        # TARJETA 3: HERRAMIENTAS DE ADMINISTRADOR (ADMIN ONLY)
        # -------------------------------------------------------------
        if rol_actual == "admin":
            card_admin = tk.Frame(self.contenedor, bg=COLOR_CARD, highlightbackground=COLOR_CARD_BORDER, highlightthickness=1)
            card_admin.pack(fill="x", pady=(0, 5), ipadx=10, ipady=10)

            tk.Label(card_admin, text="⚙️  PANEL DE ADMINISTRACIÓN", font=(FONT_MAIN, 9, "bold"), fg=COLOR_PURPLE, bg=COLOR_CARD).pack(anchor="w", padx=15, pady=(5, 8))

            grid_admin1 = tk.Frame(card_admin, bg=COLOR_CARD)
            grid_admin1.pack(fill="x", padx=15, pady=(0, 8))

            self.btn_admin = BotonRedondeado(grid_admin1, text="📋 REGISTROS LOGS", command=self.abrir_ventana_logs, bg=COLOR_PURPLE, hover_bg=COLOR_PURPLE_HOVER, fg=COLOR_INPUT, width=198, height=36)
            self.btn_admin.pack(side="left", expand=True, padx=(0, 4))

            self.btn_gestion_usr = BotonRedondeado(grid_admin1, text="👥 GESTIÓN USUARIOS", command=self.abrir_ventana_gestion_usuarios, bg=COLOR_GREEN, hover_bg=COLOR_GREEN_HOVER, fg=COLOR_INPUT, width=198, height=36)
            self.btn_gestion_usr.pack(side="right", expand=True, padx=(4, 0))

            self.btn_admin_todo = BotonRedondeado(card_admin, text="🗄️ INSPECTOR GLOBAL DE BASE DE DATOS", command=self.abrir_ventana_bd_completa, bg=COLOR_BLUE, hover_bg=COLOR_BLUE_HOVER, fg=COLOR_INPUT, width=405, height=36)
            self.btn_admin_todo.pack(fill="x", padx=15)

    def ejecutar_proceso_nfc(self, forzar_fallo):
        self.btn_abrir.configurar_estado("disabled")
        self.btn_fallar.configurar_estado("disabled")
        if hasattr(self, 'btn_admin'): self.btn_admin.configurar_estado("disabled")
        if hasattr(self, 'btn_admin_todo'): self.btn_admin_todo.configurar_estado("disabled")
        if hasattr(self, 'btn_gestion_usr'): self.btn_gestion_usr.configurar_estado("disabled")

        hilo_hardware = threading.Thread(target=simulacion_nfc_thread, args=(self.usuario_actual, forzar_fallo))
        hilo_hardware.start()
        self.escuchar_cola()

    def escuchar_cola(self):
        try:
            mensaje = cola_mensajes.get_nowait()
            if mensaje == "TERMINADO":
                self.label_estado.config(text="🟢  SISTEMA LISTO", fg=COLOR_GREEN)
                self.btn_abrir.configurar_estado("normal", COLOR_GREEN)
                self.btn_fallar.configurar_estado("normal", COLOR_RED)
                if hasattr(self, 'btn_admin'): self.btn_admin.configurar_estado("normal", COLOR_PURPLE)
                if hasattr(self, 'btn_admin_todo'): self.btn_admin_todo.configurar_estado("normal", COLOR_BLUE)
                if hasattr(self, 'btn_gestion_usr'): self.btn_gestion_usr.configurar_estado("normal", COLOR_GREEN)
                return
            
            if "ERROR" in mensaje:
                self.label_estado.config(text=f"🔴  {mensaje}", fg=COLOR_RED)
            else:
                self.label_estado.config(text=f"⏳  {mensaje}", fg=COLOR_BLUE)
                
            self.root.after(100, self.escuchar_cola)
        except:
            self.root.after(100, self.escuchar_cola)

    # --- VENTANA DE CHAT INTEGRADO ---
    def abrir_ventana_chat(self):
        v_chat = tk.Toplevel(self.root)
        v_chat.title(f"Centro de Mensajes - {self.usuario_actual}")
        v_chat.geometry("520x580")
        v_chat.configure(bg=COLOR_BG)

        notebook = ttk.Notebook(v_chat)
        notebook.pack(expand=True, fill="both", padx=12, pady=12)

        tab_general = tk.Frame(notebook, bg=COLOR_CARD)
        notebook.add(tab_general, text="📢 Chat General")

        tab_privado = tk.Frame(notebook, bg=COLOR_CARD)
        notebook.add(tab_privado, text="👤 Chat 1 a 1")

        def crear_caja_chat(parent):
            txt = tk.Text(parent, bg=COLOR_INPUT, fg=COLOR_TEXT, bd=0, font=(FONT_MAIN, 9), state="disabled", wrap="word", selectbackground=COLOR_BLUE)
            txt.tag_config("system", foreground=COLOR_SUBTEXT, font=(FONT_MAIN, 8, "italic"))
            txt.tag_config("global", foreground=COLOR_BLUE, font=(FONT_MAIN, 9, "bold"))
            txt.tag_config("private", foreground=COLOR_PURPLE, font=(FONT_MAIN, 9, "bold"))
            txt.tag_config("text", foreground=COLOR_TEXT, font=(FONT_MAIN, 9))
            return txt

        # Chat General
        txt_gen = crear_caja_chat(tab_general)
        txt_gen.pack(expand=True, fill="both", padx=10, pady=10)

        frame_gen_input = tk.Frame(tab_general, bg=COLOR_CARD)
        frame_gen_input.pack(fill="x", padx=10, pady=(0, 10))
        entry_gen = tk.Entry(frame_gen_input, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT, bd=0, font=(FONT_MAIN, 10))
        entry_gen.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))

        # Chat Privado
        frame_top_p = tk.Frame(tab_privado, bg=COLOR_CARD)
        frame_top_p.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(frame_top_p, text="Destinatario:", fg=COLOR_TEXT, bg=COLOR_CARD, font=(FONT_MAIN, 9, "bold")).pack(side="left")
        
        usuarios_disp = [u for u in obtener_todos_los_usuarios() if u != self.usuario_actual]
        combo_dest = ttk.Combobox(frame_top_p, values=usuarios_disp, state="readonly", width=18)
        if usuarios_disp:
            combo_dest.current(0)
        combo_dest.pack(side="left", padx=8)

        txt_priv = crear_caja_chat(tab_privado)
        txt_priv.pack(expand=True, fill="both", padx=10, pady=5)

        frame_priv_input = tk.Frame(tab_privado, bg=COLOR_CARD)
        frame_priv_input.pack(fill="x", padx=10, pady=(0, 10))
        entry_priv = tk.Entry(frame_priv_input, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT, bd=0, font=(FONT_MAIN, 10))
        entry_priv.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))

        def recibir_mensaje_servidor(raw):
            partes = raw.split("|", 2)
            header = partes[0]

            if header == "SYSTEM":
                msg = partes[1]
                _append_formatted(txt_gen, [("[SISTEMA] ", "system"), (f"{msg}\n", "system")])
                _append_formatted(txt_priv, [("[SISTEMA] ", "system"), (f"{msg}\n", "system")])

            elif header == "GLOBAL":
                remitente = partes[1]
                contenido = partes[2]
                if es_bloqueado_db(self.usuario_actual, remitente):
                    return
                _append_formatted(txt_gen, [(f"{remitente}: ", "global"), (f"{contenido}\n", "text")])

            elif header == "PRIVATE":
                remitente = partes[1]
                contenido = partes[2]
                if es_bloqueado_db(self.usuario_actual, remitente):
                    return
                _append_formatted(txt_priv, [(f"[{remitente} ➔ Mí]: ", "private"), (f"{contenido}\n", "text")])

        def _append_formatted(widget_txt, partes_tags):
            widget_txt.config(state="normal")
            for texto, tag in partes_tags:
                widget_txt.insert("end", texto, tag)
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

        btn_send_gen = BotonRedondeado(frame_gen_input, text="ENVIAR", command=enviar_gen, bg=COLOR_GREEN, hover_bg=COLOR_GREEN_HOVER, fg=COLOR_INPUT, width=80, height=32)
        btn_send_gen.pack(side="right")

        btn_send_priv = BotonRedondeado(frame_priv_input, text="ENVIAR 1a1", command=enviar_priv, bg=COLOR_BLUE, hover_bg=COLOR_BLUE_HOVER, fg=COLOR_INPUT, width=95, height=32)
        btn_send_priv.pack(side="right")

        v_chat.protocol("WM_DELETE_WINDOW", lambda: (cliente.desconectar(), v_chat.destroy()))

    # --- VENTANA: LISTA NEGRA PERSONAL ---
    def abrir_ventana_lista_negra_personal(self):
        v_bl = tk.Toplevel(self.root)
        v_bl.title("Mi Lista Negra Personal")
        v_bl.geometry("400x440")
        v_bl.configure(bg=COLOR_BG)

        tk.Label(v_bl, text="CONTACTOS BLOQUEADOS", font=(FONT_MAIN, 11, "bold"), fg=COLOR_PURPLE, bg=COLOR_BG).pack(pady=(15, 2))
        tk.Label(v_bl, text="Los mensajes de usuarios bloqueados serán ocultados automáticamente", font=(FONT_MAIN, 8), fg=COLOR_SUBTEXT, bg=COLOR_BG).pack(pady=(0, 10))

        lista_box = tk.Listbox(v_bl, bg=COLOR_INPUT, fg=COLOR_RED, bd=0, highlightthickness=0, font=(FONT_MAIN, 10), selectbackground=COLOR_CARD)
        lista_box.pack(expand=True, fill="both", padx=20, pady=5)

        def actualizar_lista():
            lista_box.delete(0, "end")
            bloqueados = obtener_bloqueados_db(self.usuario_actual)
            for b in bloqueados:
                lista_box.insert("end", f" 🚫  {b}")

        actualizar_lista()

        frame_add = tk.Frame(v_bl, bg=COLOR_BG)
        frame_add.pack(fill="x", padx=20, pady=10)

        todos_usrs = [u for u in obtener_todos_los_usuarios() if u != self.usuario_actual]
        combo_block = ttk.Combobox(frame_add, values=todos_usrs, state="readonly", width=14)
        if todos_usrs:
            combo_block.current(0)
        combo_block.pack(side="left", padx=(0, 8))

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
            usr_target = linea.replace(" 🚫  ", "").strip()
            if desbloquear_usuario_db(self.usuario_actual, usr_target):
                messagebox.showinfo("Éxito", f"Usuario '{usr_target}' desbloqueado.")
                actualizar_lista()

        btn_add = BotonRedondeado(frame_add, text="BLOQUEAR", command=bloquear_sel, bg=COLOR_RED, hover_bg=COLOR_RED_HOVER, fg=COLOR_INPUT, width=110, height=32)
        btn_add.pack(side="left")

        btn_del = BotonRedondeado(v_bl, text="DESBLOQUEAR SELECCIONADO", command=desbloquear_sel, bg=COLOR_GREEN, hover_bg=COLOR_GREEN_HOVER, fg=COLOR_INPUT, width=240, height=35)
        btn_del.pack(pady=(5, 15))

    # --- VENTANA ADMIN 1: REGISTROS LOGS ---
    def abrir_ventana_logs(self):
        v_logs = tk.Toplevel(self.root)
        v_logs.title("Logs de Accesos")
        v_logs.geometry("440x440")
        v_logs.configure(bg=COLOR_BG)

        tk.Label(v_logs, text="HISTORIAL DE REGISTROS DE ACCESO", font=(FONT_MAIN, 11, "bold"), fg=COLOR_TEXT, bg=COLOR_BG).pack(pady=15)
        frame_scroll = tk.Frame(v_logs, bg=COLOR_BG)
        frame_scroll.pack(expand=True, fill="both", padx=20, pady=5)

        scroll = tk.Scrollbar(frame_scroll)
        scroll.pack(side="right", fill="y")

        lista = tk.Listbox(frame_scroll, bg=COLOR_INPUT, fg=COLOR_TEXT, bd=0, highlightthickness=0, font=("Consolas", 9), yscrollcommand=scroll.set)
        lista.pack(expand=True, fill="both", side="left")
        scroll.config(command=lista.yview)

        registros = obtener_registros_acceso()
        for fecha, tipo, estado in registros:
            lista.insert("end", f" [{fecha}] {tipo} ➔ {estado}")

        btn_cerrar = BotonRedondeado(v_logs, text="CERRAR VENTANA", command=v_logs.destroy, bg=COLOR_SUBTEXT, fg=COLOR_INPUT, width=160, height=35)
        btn_cerrar.pack(pady=15)

    # --- VENTANA ADMIN 2: GESTIÓN DE USUARIOS ---
    def abrir_ventana_gestion_usuarios(self):
        v_usr = tk.Toplevel(self.root)
        v_usr.title("Gestión de Usuarios")
        v_usr.geometry("480x460")
        v_usr.configure(bg=COLOR_BG)

        tk.Label(v_usr, text="ADMINISTRACIÓN DE USUARIOS", font=(FONT_MAIN, 11, "bold"), fg=COLOR_TEXT, bg=COLOR_BG).pack(pady=15)
        
        frame_scroll = tk.Frame(v_usr, bg=COLOR_BG)
        frame_scroll.pack(expand=True, fill="both", padx=20, pady=5)

        scroll = tk.Scrollbar(frame_scroll)
        scroll.pack(side="right", fill="y")

        lista_usr = tk.Listbox(frame_scroll, bg=COLOR_INPUT, fg=COLOR_TEXT, bd=0, highlightthickness=0, font=("Consolas", 10), yscrollcommand=scroll.set)
        lista_usr.pack(expand=True, fill="both", side="left")
        scroll.config(command=lista_usr.yview)

        usuarios_cache = []

        def cargar_usuarios():
            lista_usr.delete(0, "end")
            usuarios_cache.clear()
            datos = obtener_todo_db()
            for row in datos["usuarios"]:
                uid, nombre, rol, nfc, _ = row
                usuarios_cache.append((uid, nombre, rol))
                lista_usr.insert("end", f" ID: {uid:<3} | User: {nombre:<10} | Rol: {rol.upper()}")

        cargar_usuarios()

        def alternar_rol():
            seleccion = lista_usr.curselection()
            if not seleccion:
                messagebox.showwarning("Atención", "Selecciona un usuario.")
                return
            uid, nombre, rol = usuarios_cache[seleccion[0]]
            
            if nombre == self.usuario_actual:
                messagebox.showerror("Error", "No puedes revocar tus propios permisos.")
                return
            
            nuevo_rol = "usuario" if rol == "admin" else "admin"
            if cambiar_rol_usuario(uid, nuevo_rol):
                messagebox.showinfo("Éxito", f"Rol actualizado a {nuevo_rol.upper()}.")
                cargar_usuarios()
                self.pantalla_puerta()

        def eliminar_usuario():
            seleccion = lista_usr.curselection()
            if not seleccion:
                messagebox.showwarning("Atención", "Selecciona un usuario.")
                return
            uid, nombre, _ = usuarios_cache[seleccion[0]]
            
            if nombre == self.usuario_actual:
                messagebox.showerror("Error", "No puedes eliminar tu propia cuenta.")
                return
            
            if messagebox.askyesno("Confirmar", f"¿Eliminar permanentemente a '{nombre}'?"):
                if eliminar_usuario_db(uid):
                    messagebox.showinfo("Éxito", "Usuario eliminado.")
                    cargar_usuarios()

        frame_btns = tk.Frame(v_usr, bg=COLOR_BG)
        frame_btns.pack(pady=15)

        btn_permiso = BotonRedondeado(frame_btns, text="CAMBIAR ROL", command=alternar_rol, bg=COLOR_BLUE, hover_bg=COLOR_BLUE_HOVER, fg=COLOR_INPUT, width=150, height=35)
        btn_permiso.pack(side="left", padx=5)

        btn_borrar = BotonRedondeado(frame_btns, text="ELIMINAR", command=eliminar_usuario, bg=COLOR_RED, hover_bg=COLOR_RED_HOVER, fg=COLOR_INPUT, width=130, height=35)
        btn_borrar.pack(side="left", padx=5)

    # --- VENTANA ADMIN 3: INSPECTOR DE BD ---
    def abrir_ventana_bd_completa(self):
        v_bd = tk.Toplevel(self.root)
        v_bd.title("Inspección Base de Datos")
        v_bd.geometry("560x520")
        v_bd.configure(bg=COLOR_BG)

        tk.Label(v_bd, text="DATABASE RELATIONAL DUMP", font=("Consolas", 11, "bold"), fg=COLOR_BLUE, bg=COLOR_BG).pack(pady=12)

        frame_text = tk.Frame(v_bd, bg=COLOR_INPUT)
        frame_text.pack(expand=True, fill="both", padx=20, pady=5)

        scroll_y = tk.Scrollbar(frame_text)
        scroll_y.pack(side="right", fill="y")

        consola = tk.Text(frame_text, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT, bd=0, font=("Consolas", 9), yscrollcommand=scroll_y.set, wrap="none")
        consola.pack(expand=True, fill="both", side="left", padx=10, pady=10)
        scroll_y.config(command=consola.yview)

        try:
            datos = obtener_todo_db()
            texto_dump = "=== TABLA: usuarios ===\n"
            texto_dump += f"{'ID':<6} | {'Nombre':<12} | {'Rol':<10} | {'UID_NFC':<12} | {'Password (SHA256)':<15}\n"
            texto_dump += "-" * 65 + "\n"
            for u in datos["usuarios"]:
                texto_dump += f"{u[0]:<6} | {u[1]:<12} | {u[2]:<10} | {u[3]:<12} | {u[4][:12]}...\n"
                
            texto_dump += "\n=== TABLA: registro_acceso ===\n"
            texto_dump += f"{'ID':<6} | {'Fecha/Hora':<20} | {'Tipo':<10} | {'Estado':<18}\n"
            texto_dump += "-" * 60 + "\n"
            if datos["accesos"]:
                for a in datos["accesos"]:
                    texto_dump += f"{a[0]:<6} | {a[1]:<20} | {a[2]:<10} | {a[3]:<18}\n"
            else:
                texto_dump += " (Sin registros de acceso)\n"

            texto_dump += "\n=== TABLA: bloqueos_usuario ===\n"
            texto_dump += f"{'Origen':<15} | {'Bloqueado':<15}\n"
            texto_dump += "-" * 35 + "\n"
            if datos["bloqueos"]:
                for b in datos["bloqueos"]:
                    texto_dump += f"{b[0]:<15} | {b[1]:<15}\n"
            else:
                texto_dump += " (Sin bloqueos personales activos)\n"

        except Exception as e:
            texto_dump = f"❌ ERROR AL LEER BD:\n{str(e)}"

        consola.insert("1.0", texto_dump)
        consola.config(state="disabled")

        btn_cerrar = BotonRedondeado(v_bd, text="CERRAR INSPECTOR", command=v_bd.destroy, bg=COLOR_SUBTEXT, fg=COLOR_INPUT, width=160, height=35)
        btn_cerrar.pack(pady=15, side="bottom")
