from PySide import QtGui
from PySide.QtCore import QThread, SIGNAL
from abc import ABCMeta, abstractmethod
import sys
import ClientView
import threading
import queue
import socket


class Update(QThread):
    def __init__(self, queue):
        QThread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            text = self.queue.get()
            if text is False:
                break
            self.emit(SIGNAL('add_post(QString)'), text)

    def message(self, text, titel):
        self.emit(SIGNAL('message(QString, QString)'), text, titel)


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


class Send(threading.Thread, Stoppable):

    def __init__(self, queue, queueR, update):
        threading.Thread.__init__(self)
        self.port = 4242
        self.host = "localhost"
        self.queue = queue
        self.con = None
        self.update = update
        self.queueR = queueR
        self.recv = None
        self.running = True

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.con:
            try:
                self.con.connect((self.host, self.port))
                self.recv = Recv(self.queueR, self.update, self.con, self)
                self.recv.start()
                while self.running:
                    text = self.queue.get()
                    if text is False:
                        break
                    self.con.send(text.encode())
            except socket.error as serr:
                self.update.message("Es konnte keine Verbindung mit den Server hergestellt werden.", "ERROR")
                self.update.queue.put(False)
                self.stopping()

    def stopping(self):
        self.running = False
        self.queue.put(False)
        self.con.close()
        if self.recv is not None:
            self.recv.stopping()


class Recv(threading.Thread, Stoppable):

    def __init__(self, queueR, update, con, send):
        threading.Thread.__init__(self)
        self.port = 4242
        self.host = "localhost"
        self.queue = queueR
        self.con = con
        self.update = update
        self.send = send
        self.running = True

    def run(self):
        while self.running:
            try:
                text = self.con.recv(1024).decode()
                self.queue.put(text)
            except ConnectionResetError:
                self.stopping()
                self.update.message("Verbindung zum Server verloren.", "ERROR")
                self.update.queue.put(False)
                self.send.stopping()
            except ConnectionAbortedError:
                self.stopping()

    def stopping(self):
        self.running = False
        if self.send.running is True:
            self.send.stopping()


class View(QtGui.QMainWindow, ClientView.Ui_MainWindow):

    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.queueR = queue.Queue()
        self.update = Update(self.queueR)
        self.connect(self.update, SIGNAL("add_post(QString)"), self.add_post)
        self.connect(self.update, SIGNAL("message(QString, QString)"), self.message)
        self.update.start()

        self.sendQ = queue.Queue()
        self.send = Send(self.sendQ, self.queueR, self.update)
        self.send.start()
        self.pushButton.clicked.connect(self.send_post)

    def send_post(self):
        text = self.lineEdit.text()
        self.sendQ.put(text)
        self.lineEdit.setText("")

    def add_post(self, text):
        self.textBrowser.append(str(text))

    def message(self, text, titel):
        QtGui.QMessageBox.critical(self, titel, text)
        self.close()

    def closeEvent(self, event):
        self.queueR.put(False)
        self.send.stopping()


def main():
    app = QtGui.QApplication(sys.argv)
    form = View()
    form.show()
    app.exec_()

if __name__ == '__main__':
    main()
