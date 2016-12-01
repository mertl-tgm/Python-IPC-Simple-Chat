import threading
import socket


class Model(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.port = 4242
        self.host = "localhost"

    def run(self):
        while True:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientsocket:
                try:
                    clientsocket.connect((self.host, self.port))
                    while True:
                        msg = input("Nachricht:")
                        clientsocket.send(msg.encode())
                        data = clientsocket.recv(1024).decode()
                        if not data:
                            clientsocket.close()
                            break
                        print("Server: %s" % data)
                        if data == "Bye!":
                            clientsocket.close()
                            break
                except socket.error as serr:
                    print("Socket error: " + serr.strerror)
