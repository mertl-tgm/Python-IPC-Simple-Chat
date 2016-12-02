from abc import ABCMeta, abstractmethod
import threading
import socket


class Model(threading.Thread):

    def __init__(self, c):
        threading.Thread.__init__(self)
        self.port = 4242
        self.threads = []
        self.c = c

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serversocket:
            serversocket.bind(("", self.port))
            serversocket.listen(5)
            try:
                while True:
                    con, addr = serversocket.accept()
                    r = Recv(con, self.c)
                    r.start()
                    self.threads += [r]
            except socket.error as serr:
                print(serr)
                print("Socket closed.")


class Recv(threading.Thread):

    def __init__(self, con, c):
        threading.Thread.__init__(self)
        self.running = True
        self.con = con
        self.c = c

    def stopping(self):
        """
        Will set running to false
        :return: None
        """
        self.running = False

    def run(self):
        while self.running:
            try:
                data = self.con.recv(1024).decode()
                if not data:
                    self.con.close()
                    break
                print("Client: %s" % data)
            except ConnectionResetError:
                self.running = False
                print("Verbindung vom Client getrennt")


class Stoppable(metaclass=ABCMeta):
    """
        @author Ertl Marvin
        @version 2016-12-02

        This class inherits from the metaclass ABCMeta, abstract base class, it offers a method stopping, which need to
        be overwritten
    """

    @abstractmethod
    def stopping(self):
        """
        Abstract method, must be overwritten, will be called, when the thread need to be stopped
        :return: None
        """
        pass

