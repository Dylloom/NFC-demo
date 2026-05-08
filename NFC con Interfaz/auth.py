from config import USER_DB

def verificar_credenciales(usuario, password):
    return USER_DB.get(usuario) == password