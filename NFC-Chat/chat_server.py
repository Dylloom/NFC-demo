import socket
import threading
from datetime import datetime
from config import HOST_CHAT, PORT_CHAT, lock_chat

class ServidorChat:
    def __init__(self, host=HOST_CHAT, port=PORT_CHAT):
        self.host = host
        self.port = port
        self.servidor = None
        self.clientes = {}  # socket -> usuario_string
        self.running = False

    def guardar_en_archivo_txt(self, mensaje):
        """IPC Método 3: Registro en archivo 'chat_historial.txt' sincronizado mediante Lock."""
        with lock_chat:
            try:
                with open("chat_historial.txt", "a", encoding="utf-8") as f:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp}] {mensaje}\n")
            except Exception as e:
                print(f"[CHAT SERVER] Error en escritura de archivo: {e}")

    def iniciar(self):
        try:
            self.servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.servidor.bind((self.host, self.port))
            self.servidor.listen(10)
            self.running = True
            print(f"[CHAT SERVER] Servidor TCP multihilo activo en {self.host}:{self.port}")

            while self.running:
                client_socket, _ = self.servidor.accept()
                # CADA CLIENTE POSEE SU PROPIO HILO INDEPENDIENTE
                hilo_cliente = threading.Thread(
                    target=self.manejar_cliente, 
                    args=(client_socket,),
                    daemon=True
                )
                hilo_cliente.start()
        except Exception as e:
            if self.running:
                print(f"[CHAT SERVER] Error de servidor: {e}")

    def manejar_cliente(self, client_socket):
        usuario = "Anónimo"
        try:
            client_socket.send("WELCOME".encode('utf-8'))
            usuario = client_socket.recv(1024).decode('utf-8').strip()
            self.clientes[client_socket] = usuario

            msg_init = f"SYSTEM|*** El usuario '{usuario}' se ha conectado al servidor ***"
            self.broadcast(msg_init)
            self.guardar_en_archivo_txt(f"CONEXIÓN: {usuario}")

            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                raw_msg = data.decode('utf-8').strip()
                if raw_msg == "/exit":
                    break

                # PROTOCOLO DE MENSAJES:
                # GLOBAL|mensaje
                # PRIVATE|destinatario|mensaje
                partes = raw_msg.split("|", 2)
                tipo = partes[0]

                if tipo == "GLOBAL":
                    contenido = partes[1]
                    out = f"GLOBAL|{usuario}|{contenido}"
                    self.broadcast(out)
                    self.guardar_en_archivo_txt(f"[CHAT GENERAL] {usuario}: {contenido}")

                elif tipo == "PRIVATE":
                    destinatario = partes[1]
                    contenido = partes[2]
                    self.enviar_privado(usuario, destinatario, contenido)
                    self.guardar_en_archivo_txt(f"[CHAT 1a1] {usuario} -> {destinatario}: {contenido}")

        except Exception as e:
            print(f"[CHAT SERVER] Desconexión de {usuario}: {e}")
        finally:
            self.desconectar_cliente(client_socket)

    def broadcast(self, mensaje_formateado):
        """Envía el mensaje a todos los clientes conectados."""
        for sock in list(self.clientes.keys()):
            try:
                sock.send(mensaje_formateado.encode('utf-8'))
            except:
                self.desconectar_cliente(sock)

    def enviar_privado(self, remitente, destinatario, mensaje):
        """Enruta un mensaje 1 a 1 entre el remitente y el destinatario específico."""
        out = f"PRIVATE|{remitente}|{mensaje}"
        enviado = False

        for sock, usr in list(self.clientes.items()):
            if usr == destinatario or usr == remitente:
                try:
                    sock.send(out.encode('utf-8'))
                    if usr == destinatario:
                        enviado = True
                except:
                    self.desconectar_cliente(sock)

        if not enviado:
            # Notificar al remitente que el destinatario no está conectado actualmente
            for sock, usr in self.clientes.items():
                if usr == remitente:
                    err_msg = f"SYSTEM|El usuario '{destinatario}' no está en línea."
                    sock.send(err_msg.encode('utf-8'))

    def desconectar_cliente(self, client_socket):
        if client_socket in self.clientes:
            usuario = self.clientes.pop(client_socket)
            msg = f"SYSTEM|*** El usuario '{usuario}' se ha desconectado ***"
            self.broadcast(msg)
            self.guardar_en_archivo_txt(f"DESCONEXIÓN: {usuario}")
        try:
            client_socket.close()
        except:
            pass

servidor_chat_instancia = ServidorChat()
