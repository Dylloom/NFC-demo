import sqlite3
import hashlib
from database import DB_NAME

def generar_hash(password: str) -> str:
    """Genera el hash SHA-256 de una contraseña utilizando la biblioteca nativa OpenSSL de Python."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verificar_credenciales(usuario, password):
    """Verifica las credenciales comparando el hash SHA-256 de la contraseña ingresada."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM usuarios WHERE Nombre = ?", (usuario,))
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            pass_hash = generar_hash(password)
            return resultado[0] == pass_hash
        return False
    except sqlite3.Error as e:
        print(f"Error en autenticación SQLite: {e}")
        return False
