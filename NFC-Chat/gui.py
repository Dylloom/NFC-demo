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
        self.root.geometry("420x720")
        self.root.configure(bg=COLOR_BG)
        
        self.usuario_actual = None
        self.contenedor = tk.Frame(self.root, bg=COLOR_BG)
        self.contenedor.pack(expand=True, fill="both", padx=20, pady=15)
        
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
        tk.Label(card, text=f"Usuario activo: {self.usuario_actual} ({rol_actual.upper()})", font=("Arial", 9, "italic"), fg=COLOR_SUBTEXT, bg=COLOR_CARD).pack(pady=(8, 2))

        self.label_estado = tk.Label(card, text="Listo para operar", font=("Arial", 11, "bold"), fg=COLOR_SUBTEXT, bg=COLOR_CARD)
        self.label_estado.pack(pady=(5, 5))
        
        # Botones de Operación NFC
        self.btn_abrir = BotonRedondeado(card, text="ABRIR PUERTA", command=lambda: self.ejecutar_proceso_nfc(False), bg=COLOR_GREEN, fg=COLOR_INPUT, width=240, height=36)
        self.btn_abrir.pack(pady=4)

        self.btn_fallar = BotonRedondeado(card, text="SIMULAR FALLO NFC", command=lambda: self.ejecutar_proceso_nfc(True), bg=COLOR_RED, fg=COLOR_INPUT, width=240, height=36)
        self.btn_fallar.pack(pady=4)

        # Botón Acceso al Chat Multi-canal
        self.btn_chat = BotonRedondeado(card, text="💬 CHAT Y CONSULTAS", command=self.abrir_ventana_chat, bg=COLOR_BLUE, fg=COLOR_INPUT, width=240, height=36)
        self.btn_chat.pack(pady=4)

        # Botón Lista Negra Personal
        self.btn_blacklist = BotonRedondeado(card, text="🚫 MI LISTA NEGRA", command=self.abrir_ventana_lista_negra_personal, bg=COLOR_PURPLE, fg=COLOR_INPUT, width=240, height=36)
        self.btn_blacklist.pack(pady=4)

        # --- HERRAMIENTAS EXCLUSIVAS DE ADMINISTRADOR ---
        if rol_actual == "admin":
            tk.Label(card, text="── Panel de Administración ──", font=("Arial", 8, "bold"), fg=COLOR_SUBTEXT, bg=COLOR_CARD).pack(pady=(8, 4))
            
            self.btn_admin = BotonRedondeado(card, text="📋 VER REGISTROS ACCESO", command=self.abrir_ventana_logs, bg=COLOR_PURPLE, fg=COLOR_INPUT, width=240, height=34)
            self.btn_admin.pack(pady=3)
            
            self.btn_admin_todo = BotonRedondeado(card, text="🗄️ VER BD COMPLETA", command=self.abrir_ventana_bd_completa, bg=COLOR_BLUE, fg=COLOR_INPUT, width=240, height=34)
            self.btn_admin_todo.pack(pady=3)

            self.btn_gestion_usr = BotonRedondeado(card, text="👥 GESTIONAR USUARIOS", command=self.abrir_ventana_gestion_usuarios, bg=COLOR_GREEN, fg=COLOR_INPUT, width=240, height=34)
            self.btn_gestion_usr.pack(pady=3)

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
                self.label_estado.config(text="Listo para operar", fg=COLOR_SUBTEXT)
                self.btn_abrir.configurar_estado("normal", COLOR_GREEN)
                self.btn_fallar.configurar_estado("normal", COLOR_RED)
                if hasattr(self, 'btn_admin'): self.btn_admin.configurar_estado("normal", COLOR_PURPLE)
                if hasattr(self, 'btn_admin_todo'): self.btn_admin_todo.configurar_estado("normal", COLOR_BLUE)
                if hasattr(self, 'btn_gestion_usr'): self.btn_gestion_usr.configurar_estado("normal", COLOR_GREEN)
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

        tab_general = tk.Frame(notebook, bg=COLOR_BG)
        notebook.add(tab_general, text="📢 Chat General (Todos)")

        tab_privado = tk.Frame(notebook, bg=COLOR_BG)
        notebook.add(tab_privado, text="👤 Chat 1 a 1 (Privado)")

        # Chat General
        txt_gen = tk.Text(tab_general, bg=COLOR_INPUT, fg=COLOR_TEXT, bd=0, font=("Consolas", 9), state="disabled")
        txt_gen.pack(expand=True, fill="both", padx=10, pady=10)

        frame_gen_input = tk.Frame(tab_general, bg=COLOR_BG)
        frame_gen_input.pack(fill="x", padx=10, pady=5)
        entry_gen = tk.Entry(frame_gen_input, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT, font=("Arial", 10))
        entry_gen.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 5))

        # Chat Privado
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
                if es_bloqueado_db(self.usuario_actual, remitente):
                    return
                _append_text(txt_gen, f"{remitente}: {contenido}")

            elif header == "PRIVATE":
                remitente = partes[1]
                contenido = partes[2]
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

    # --- VENTANA ADMIN 1: REGISTROS ACCESO ---
    def abrir_ventana_logs(self):
        ventana_logs = tk.Toplevel(self.root)
        ventana_logs.title("Logs de Accesos")
        ventana_logs.geometry("420x420")
        ventana_logs.configure(bg=COLOR_BG)
        ventana_logs.transient(self.root)
        ventana_logs.grab_set()

        tk.Label(ventana_logs, text="HISTORIAL DE REGISTROS DE ACCESO", font=("Arial", 11, "bold"), fg=COLOR_TEXT, bg=COLOR_BG).pack(pady=15)
        frame_scroll = tk.Frame(ventana_logs, bg=COLOR_BG)
        frame_scroll.pack(expand=True, fill="both", padx=20, pady=5)

        scroll = tk.Scrollbar(frame_scroll)
        scroll.pack(side="right", fill="y")

        lista = tk.Listbox(frame_scroll, bg=COLOR_INPUT, fg=COLOR_TEXT, bd=0, highlightthickness=0, font=("Consolas", 9), yscrollcommand=scroll.set)
        lista.pack(expand=True, fill="both", side="left")
        scroll.config(command=lista.yview)

        registros = obtener_registros_acceso()
        for fecha, tipo, estado in registros:
            lista.insert("end", f" [{fecha}] {tipo} -> {estado}")

        if not registros:
            lista.insert("end", " No se registran eventos en registro_acceso.")

        btn_cerrar = BotonRedondeado(ventana_logs, text="CERRAR VENTANA", command=ventana_logs.destroy, bg=COLOR_SUBTEXT, fg=COLOR_INPUT, width=150, height=35)
        btn_cerrar.pack(pady=15)

    # --- VENTANA ADMIN 2: GESTIÓN DE USUARIOS ---
    def abrir_ventana_gestion_usuarios(self):
        ventana_gestion = tk.Toplevel(self.root)
        ventana_gestion.title("Gestión de Usuarios")
        ventana_gestion.geometry("460x450")
        ventana_gestion.configure(bg=COLOR_BG)
        ventana_gestion.transient(self.root)
        ventana_gestion.grab_set()

        tk.Label(ventana_gestion, text="GESTIÓN DE PERMISOS TEMPORALES", font=("Arial", 11, "bold"), fg=COLOR_TEXT, bg=COLOR_BG).pack(pady=15)
        
        frame_scroll = tk.Frame(ventana_gestion, bg=COLOR_BG)
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
                messagebox.showwarning("Atención", "Selecciona un usuario de la lista.")
                return
            uid, nombre, rol = usuarios_cache[seleccion[0]]
            
            if nombre == self.usuario_actual:
                messagebox.showerror("Error", "No puedes revocar tus propios permisos.")
                return
            
            nuevo_rol = "usuario" if rol == "admin" else "admin"
            if cambiar_rol_usuario(uid, nuevo_rol):
                messagebox.showinfo("Éxito", f"Permisos actualizados para '{nombre}' a {nuevo_rol.upper()}.")
                cargar_usuarios()
                self.pantalla_puerta()

        def eliminar_usuario():
            seleccion = lista_usr.curselection()
            if not seleccion:
                messagebox.showwarning("Atención", "Selecciona un usuario de la lista.")
                return
            uid, nombre, _ = usuarios_cache[seleccion[0]]
            
            if nombre == self.usuario_actual:
                messagebox.showerror("Error", "No puedes eliminar tu propia cuenta en ejecución.")
                return
            
            if messagebox.askyesno("Confirmar", f"¿Seguro que deseas eliminar permanentemente a '{nombre}'?"):
                if eliminar_usuario_db(uid):
                    messagebox.showinfo("Éxito", f"Usuario '{nombre}' eliminado correctamente.")
                    cargar_usuarios()

        frame_btns = tk.Frame(ventana_gestion, bg=COLOR_BG)
        frame_btns.pack(pady=20)

        btn_permiso = BotonRedondeado(frame_btns, text="DAR/QUITAR ADMIN", command=alternar_rol, bg=COLOR_BLUE, fg=COLOR_INPUT, width=170, height=35)
        btn_permiso.pack(side="left", padx=5)

        btn_borrar = BotonRedondeado(frame_btns, text="ELIMINAR USUARIO", command=eliminar_usuario, bg=COLOR_RED, fg=COLOR_INPUT, width=150, height=35)
        btn_borrar.pack(side="left", padx=5)

    # --- VENTANA ADMIN 3: INSPECTOR DE BD ---
    def abrir_ventana_bd_completa(self):
        ventana_todo = tk.Toplevel(self.root)
        ventana_todo.title("Inspección Total Base de Datos")
        ventana_todo.geometry("540x520")
        ventana_todo.configure(bg=COLOR_BG)
        ventana_todo.transient(self.root)
        ventana_todo.grab_set()

        tk.Label(ventana_todo, text="DATABASE RELATIONAL DUMP", font=("Consolas", 11, "bold"), fg=COLOR_BLUE, bg=COLOR_BG).pack(pady=12)

        frame_text = tk.Frame(ventana_todo, bg=COLOR_INPUT)
        frame_text.pack(expand=True, fill="both", padx=20, pady=5)

        scroll_y = tk.Scrollbar(frame_text)
        scroll_y.pack(side="right", fill="y")

        consola = tk.Text(frame_text, bg=COLOR_INPUT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT, selectbackground=COLOR_BLUE, bd=0, highlightthickness=0, font=("Consolas", 9), yscrollcommand=scroll_y.set, wrap="none")
        consola.pack(expand=True, fill="both", side="left", padx=10, pady=10)
        scroll_y.config(command=consola.yview)

        try:
            datos = obtener_todo_db()
            texto_dump = "=== TABLA: usuarios ===\n"
            texto_dump += f"{'ID_Usuario':<12} | {'Nombre':<12} | {'Rol':<10} | {'UID_NFC':<12} | {'Password (SHA256)':<15}\n"
            texto_dump += "-" * 70 + "\n"
            for u in datos["usuarios"]:
                texto_dump += f"{u[0]:<12} | {u[1]:<12} | {u[2]:<10} | {u[3]:<12} | {u[4][:12]}...\n"
                
            texto_dump += "\n=== TABLA: registro_acceso ===\n"
            texto_dump += f"{'ID_log':<8} | {'fecha_hora':<20} | {'tipo_acceso':<12} | {'estado':<18}\n"
            texto_dump += "-" * 65 + "\n"
            if datos["accesos"]:
                for a in datos["accesos"]:
                    texto_dump += f"{a[0]:<8} | {a[1]:<20} | {a[2]:<12} | {a[3]:<18}\n"
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

        btn_cerrar = BotonRedondeado(ventana_todo, text="CERRAR INSPECTOR", command=ventana_todo.destroy, bg=COLOR_SUBTEXT, fg=COLOR_INPUT, width=160, height=35)
        btn_cerrar.pack(pady=15, side="bottom")
