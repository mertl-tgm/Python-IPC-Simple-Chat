import threading
import socket


class Model(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.port = 4444

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serversocket:
            serversocket.bind(("localhost", self.port))
            serversocket.listen(5)
            try:
                print("Auf client warten...")
                serversocket.accept()
                print("Client verbunden! Warte auf Nachricht...")
                while True:
                    data = serversocket.recv(1024).decode()
                    if not data:
                        serversocket.close()
                        break
                    print("Client: %s" % data)
                    if data == "exit":
                        serversocket.send("Bye!".encode())
                        serversocket.close()
                        break
                    else:
                        msg = input("Antwort an Client: ")
                        serversocket.send(msg.encode())
            except socket.error as serr:
                print("Socket closed.")
