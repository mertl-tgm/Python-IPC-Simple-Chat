from PySide import QtGui
from PySide.QtCore import QThread, SIGNAL
from abc import ABCMeta, abstractmethod
import sys
import ServerView
import threading
import queue
import socket


class Update(QThread):
    def __init__(self):
        QThread.__init__(self)
        self.queue = queue.Queue()
        self.model = Model(self.queue)

    def run(self):
        self.model.start()
        while True:
            text = self.queue.get()
            self.emit(SIGNAL('add_post(QString)'), text)

    def send(self, text):
        self.model.send(text)


class Model(threading.Thread):

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.port = 4242
        self.threads = []
        self.queue = queue

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serversocket:
            serversocket.bind(("", self.port))
            serversocket.listen(5)
            try:
                while True:
                    con, addr = serversocket.accept()
                    r = Recv(con, self.queue)
                    r.start()
                    self.threads += [r]
            except socket.error as serr:
                print(serr)
                print("Socket closed.")

    def send(self, text):
        for t in self.threads:
            t.send(text)


class Recv(threading.Thread):

    def __init__(self, con, queue):
        threading.Thread.__init__(self)
        self.running = True
        self.con = con
        self.queue = queue

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
                self.queue.put("Client: %s" % data)
            except ConnectionResetError:
                self.running = False
                print("Verbindung vom Client getrennt")

    def send(self, text):
        self.con.send(text.encode())


class View(QtGui.QMainWindow, ServerView.Ui_MainWindow):

    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.update = Update()
        self.connect(self.update, SIGNAL("add_post(QString)"), self.add_post)
        self.update.start()

    def add_post(self, text):
        self.textBrowser_2.append(str(text))
        self.update.send(text)

    def add_client(self, text):
        self.textBrowser.append(str(text))

    def done(self):
        self.btn_stop.setEnabled(False)
        self.btn_start.setEnabled(True)
        self.progress_bar.setValue(0)
        QtGui.QMessageBox.information(self, "Done!", "Done fetching posts!")


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
