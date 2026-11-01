import socket
import threading

class ClienteChat:
    def __init__(self, host, port, usuario, callback_mensaje):
        self.host = host
        self.port = port
        self.usuario = usuario
        self.callback_mensaje = callback_mensaje
        self.socket = None
        self.conectado = False

    def conectar(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.socket.recv(1024)
            self.socket.send(self.usuario.encode('utf-8'))
            self.conectado = True

            hilo_escucha = threading.Thread(target=self._escuchar, daemon=True)
            hilo_escucha.start()
            return True, "OK"
        except Exception as e:
            self.conectado = False
            return False, str(e)

    def _escuchar(self):
        while self.conectado:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                self.callback_mensaje(data.decode('utf-8'))
            except:
                break
        self.conectado = False

    def enviar_global(self, texto):
        if self.conectado and self.socket:
            try:
                payload = f"GLOBAL|{texto}"
                self.socket.send(payload.encode('utf-8'))
            except:
                pass

    def enviar_privado(self, destinatario, texto):
        if self.conectado and self.socket:
            try:
                payload = f"PRIVATE|{destinatario}|{texto}"
                self.socket.send(payload.encode('utf-8'))
            except:
                pass

    def desconectar(self):
        self.conectado = False
        if self.socket:
            try:
                self.socket.send("/exit".encode('utf-8'))
                self.socket.close()
            except:
                pass
