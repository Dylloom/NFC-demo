import sqlite3

DB_NAME = "seguridad_taller.db"

def inicializar_base_datos():
    """Crea la base de datos y las tablas de forma segura SOLO si no existen."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 'IF NOT EXISTS' asegura que no se sobreescriba ni falle si el archivo ya existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accesos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            fecha_hora TEXT NOT NULL
        )
    """)
    
    # Insertar usuarios iniciales solo si la tabla está completamente vacía
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        usuarios_defecto = [("admin", "1234"), ("andy", "tonotos67")]
        cursor.executemany("INSERT INTO usuarios (usuario, password) VALUES (?, ?)", usuarios_defecto)
        conn.commit()
        
    conn.close()

def registrar_usuario(usuario, password):
    """Inserta un nuevo usuario en la base de datos de forma segura."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (usuario, password) VALUES (?, ?)", (usuario, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        # Esto salta automáticamente si el usuario ya existe por la regla UNIQUE
        return False
    except sqlite3.Error as e:
        print(f"Error en SQLite al registrar: {e}")
        return False

def obtener_registros_acceso():
    """Devuelve el historial de accesos ordenado por el más reciente."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT usuario, fecha_hora FROM accesos ORDER BY id DESC")
    filas = cursor.fetchall()
    conn.close()
    return filas

def obtener_todo_db():
    """Devuelve un diccionario con los datos completos de todas las tablas."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, usuario, password FROM usuarios ORDER BY id ASC")
    usuarios = cursor.fetchall()
    
    cursor.execute("SELECT id, usuario, fecha_hora FROM accesos ORDER BY id ASC")
    accesos = cursor.fetchall()
    
    conn.close()
    return {"usuarios": usuarios, "accesos": accesos}