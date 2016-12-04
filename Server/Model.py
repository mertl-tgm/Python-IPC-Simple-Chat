from abc import ABCMeta, abstractmethod
import threading
import socket
import time
from PySide.QtCore import QThread, SIGNAL


class Model(QThread):

    def __init__(self, c):
        QThread.__init__(self)
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


class Recv(QThread):

    def __init__(self, con, c):
        QThread.__init__(self)
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
                self.c.view.textBrowser_2.setText("TEST")
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


class WatchDog(threading.Thread):
    """
        @author Ertl Marvin
        @version 2016-11-26

        This class inherits from thread, in the run method the thread wait till the stoptime is reached and then call
        stopping in all threads

            :ivar int stoptime:           Indicates when the all threads will be stopped and finished
            :ivar [] threads:             A list with all threads, which should be secured by the watchdog
    """

    def __init__(self, stoptime, *threads):
        """
        Initial the base class thread and and set the stoptime, threads list
        :param int stoptime:    How long the threads will be running
        :param [] threads:      List of all threads
        """
        threading.Thread.__init__(self)
        self.stoptime = stoptime
        self.threads = threads

    def run(self):
        """
        The run method will wait till the given time is reached and then call stopping in all threads from the list
        :return: None
        """
        start = time.time()
        end = start + self.stoptime

        while time.time() < end:
            time.sleep(0.9)

        for t in self.threads:
            t.stopping()
