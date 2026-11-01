import sqlite3
import hashlib

DB_NAME = "seguridad_taller.db"

def generar_hash(password: str) -> str:
    """Hash SHA-256 utilizando OpenSSL nativo."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def inicializar_base_datos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabla: usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            ID_Usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            Nombre TEXT UNIQUE NOT NULL,
            Rol TEXT NOT NULL,
            UID_NFC TEXT,
            password TEXT NOT NULL
        )
    """)
    
    # Tabla: registro_acceso
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registro_acceso (
            ID_log INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT NOT NULL,
            tipo_acceso TEXT NOT NULL,
            estado TEXT NOT NULL
        )
    """)
    
    # Tabla: bloqueos_usuario (LISTA NEGRA PERSONAL)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bloqueos_usuario (
            usuario_origen TEXT NOT NULL,
            usuario_bloqueado TEXT NOT NULL,
            PRIMARY KEY (usuario_origen, usuario_bloqueado)
        )
    """)

    # Tabla: app
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app (
            id_app INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            version TEXT NOT NULL
        )
    """)
    
    # Usuarios iniciales
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        usuarios_defecto = [
            ("admin", "admin", "NFC-ADMIN-01", generar_hash("1234")), 
            ("andy", "usuario", "NFC-USER-02", generar_hash("tonotos67")),
            ("maria", "usuario", "NFC-USER-03", generar_hash("maria123"))
        ]
        cursor.executemany("INSERT INTO usuarios (Nombre, Rol, UID_NFC, password) VALUES (?, ?, ?, ?)", usuarios_defecto)
        
    conn.commit()
    conn.close()

def registrar_usuario(usuario, password):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (Nombre, Rol, UID_NFC, password) VALUES (?, ?, ?, ?)", 
            (usuario, "usuario", "NFC-TEMP", generar_hash(password))
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        return False

# --- GESTIÓN DE LISTA NEGRA PERSONAL DE CADA USUARIO ---
def bloquear_usuario_db(usuario_origen, usuario_bloqueado):
    """Agrega a un usuario a la lista negra personal del usuario_origen."""
    if usuario_origen == usuario_bloqueado:
        return False
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO bloqueos_usuario (usuario_origen, usuario_bloqueado) VALUES (?, ?)", 
                       (usuario_origen, usuario_bloqueado))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        return False

def desbloquear_usuario_db(usuario_origen, usuario_bloqueado):
    """Elimina a un usuario de la lista negra personal."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bloqueos_usuario WHERE usuario_origen = ? AND usuario_bloqueado = ?", 
                       (usuario_origen, usuario_bloqueado))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        return False

def obtener_bloqueados_db(usuario_origen):
    """Retorna la lista de usuarios bloqueados por el usuario especificado."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT usuario_bloqueado FROM bloqueos_usuario WHERE usuario_origen = ?", (usuario_origen,))
        filas = [r[0] for r in cursor.fetchall()]
        conn.close()
        return filas
    except sqlite3.Error:
        return []

def es_bloqueado_db(usuario_origen, usuario_evaluado):
    """Consulta si usuario_origen tiene bloqueado a usuario_evaluado."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM bloqueos_usuario WHERE usuario_origen = ? AND usuario_bloqueado = ?", 
                       (usuario_origen, usuario_evaluado))
        res = cursor.fetchone()
        conn.close()
        return res is not None
    except sqlite3.Error:
        return False

def obtener_todos_los_usuarios():
    """Devuelve el listado de nombres de todos los usuarios registrados."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT Nombre FROM usuarios ORDER BY Nombre ASC")
        filas = [r[0] for r in cursor.fetchall()]
        conn.close()
        return filas
    except sqlite3.Error:
        return []

def obtener_rol(usuario):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT Rol FROM usuarios WHERE Nombre = ?", (usuario,))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else "usuario"
    except sqlite3.Error:
        return "usuario"

def obtener_registros_acceso():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT fecha_hora, tipo_acceso, estado FROM registro_acceso ORDER BY ID_log DESC")
    filas = cursor.fetchall()
    conn.close()
    return filas

def obtener_todo_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT ID_Usuario, Nombre, Rol, UID_NFC, password FROM usuarios ORDER BY ID_Usuario ASC")
    usuarios = cursor.fetchall()
    cursor.execute("SELECT ID_log, fecha_hora, tipo_acceso, estado FROM registro_acceso ORDER BY ID_log ASC")
    accesos = cursor.fetchall()
    cursor.execute("SELECT usuario_origen, usuario_bloqueado FROM bloqueos_usuario")
    bloqueos = cursor.fetchall()
    conn.close()
    return {"usuarios": usuarios, "accesos": accesos, "bloqueos": bloqueos}
