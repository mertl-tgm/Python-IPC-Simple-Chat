import threading
import socket


class Model(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.port = 4242

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serversocket:
            serversocket.bind(("", self.port))
            serversocket.listen(5)
            try:
                while True:
                    print("Auf client warten...")
                    con, addr = serversocket.accept()
                    print("Client verbunden! Warte auf Nachricht...")
                    while True:
                        data = con.recv(1024).decode()
                        if not data:
                            con.close()
                            break
                        print("Client: %s" % data)
                        if data == "exit":
                            con.send("Bye!".encode())
                            con.close()
                            break
                        else:
                            msg = input("Antwort an Client: ")
                            con.send(msg.encode())
            except socket.error as serr:
                print(serr)
                print("Socket closed.")
