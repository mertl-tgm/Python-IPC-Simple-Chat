from PySide import QtGui
from PySide.QtCore import QThread, SIGNAL
from abc import ABCMeta, abstractmethod
import sys
import ClientView
import threading
import queue
import socket
import time


class Update(QThread):
    def __init__(self, queue):
        QThread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            text = self.queue.get()
            self.emit(SIGNAL('add_post(QString)'), text)


class Send(threading.Thread):

    def __init__(self, queue, queueR):
        threading.Thread.__init__(self)
        self.port = 4242
        self.host = "localhost"
        self.queue = queue
        self.con = None
        self.recv = Recv(self, queueR)
        self.recv.start()

    def run(self):
        while True:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.con:
                try:
                    self.con.connect((self.host, self.port))
                    while True:
                        text = self.queue.get()
                        self.con.send(text.encode())
                except socket.error as serr:
                    print("Socket error: " + serr.strerror)


class Recv(threading.Thread):

    def __init__(self, send, queue):
        threading.Thread.__init__(self)
        self.port = 4242
        self.host = "localhost"
        self.queue = queue
        self.send = send

    def run(self):
        while True:
            time.sleep(1)
            self.con = self.send.con
            if self.con is not None:
                break
        while True:
            try:
                text = self.con.recv(1024).decode()
                self.queue.put(text)
            except ConnectionResetError:
                QtGui.QMessageBox.information(self, "ERROR!", "Verbindung zum Server verloren.")


class View(QtGui.QMainWindow, ClientView.Ui_MainWindow):

    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.queueR = queue.Queue()
        self.update = Update(self.queueR)
        self.connect(self.update, SIGNAL("add_post(QString)"), self.add_post)
        self.update.start()

        self.sendQ = queue.Queue()
        self.send = Send(self.sendQ, self.queueR)
        self.send.start()
        self.pushButton.clicked.connect(self.send_post)

    def send_post(self):
        text = self.lineEdit.text()
        self.sendQ.put(text)
        self.lineEdit.setText("")

    def add_post(self, text):
        self.textBrowser.append(str(text))

    def message(self, text, titel):
        QtGui.QMessageBox.information(self, "ERROR!", "Verbindung zum Server verloren.")


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


def main():
    app = QtGui.QApplication(sys.argv)
    form = View()
    form.show()
    app.exec_()

if __name__ == '__main__':
    main()