from PySide import QtGui
from PySide.QtCore import QThread, SIGNAL
from abc import ABCMeta, abstractmethod
import sys
import ServerView
import threading
import queue
import socket


class Update(QThread):

    def __init__(self, queue):
        QThread.__init__(self)
        self.queue = queue
        self.model = Model(self.queue, self)

    def run(self):
        self.model.start()
        while True:
            text = self.queue.get()
            if text is False:
                break
            self.emit(SIGNAL('add_post(QString)'), text)
        self.model.stopping()
        self.model.join()

    def send(self, text):
        self.model.send(text)

    def set_client(self, text):
        self.emit(SIGNAL('set_client(QString)'), text)

    def remove_client(self, text):
        self.emit(SIGNAL('remove_client(QString)'), text)


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


class Model(threading.Thread, Stoppable):

    def __init__(self, queue, update):
        threading.Thread.__init__(self)
        self.port = 4242
        self.threads = []
        self.queue = queue
        self.update = update
        self.running = True
        self.serversocket = None

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.serversocket:
            self.serversocket.bind(("", self.port))
            self.serversocket.listen(5)
            try:
                while self.running:
                    con, addr = self.serversocket.accept()
                    r = Recv(con, self.queue, "Client " + str(len(self.threads) + 1), self.update)
                    r.start()
                    self.threads += [r]
                    self.update.set_client(r.name)
            except socket.error as serr:
                pass

            for t in self.threads:
                t.con.close()
                t.stopping()
                t.join()

    def send(self, text):
        for t in self.threads:
            t.send(text)

    def stopping(self):
        self.running = False
        self.serversocket.close()


class Recv(threading.Thread, Stoppable):

    def __init__(self, con, queue, name, update):
        threading.Thread.__init__(self)
        self.running = True
        self.con = con
        self.queue = queue
        self.name = name
        self.update = update

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
                self.queue.put(self.name + ": %s" % data)
            except ConnectionResetError:
                self.running = False
                self.update.remove_client(self.name)
            except ConnectionAbortedError:
                pass

    def send(self, text):
        self.con.send(text.encode())


class View(QtGui.QMainWindow, ServerView.Ui_MainWindow):

    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.queue = queue.Queue()
        self.update = Update(self.queue)
        self.connect(self.update, SIGNAL("add_post(QString)"), self.add_post)
        self.connect(self.update, SIGNAL("set_client(QString)"), self.set_client)
        self.connect(self.update, SIGNAL("remove_client(QString)"), self.remove_client)
        self.update.start()
        self.names = []

    def add_post(self, text):
        self.textBrowser_2.append(str(text))
        self.update.send(text)

    def set_client(self, text):
        self.textBrowser.append(str(text))
        self.names += [text]

    def remove_client(self, text):
        name2 = []
        for name in self.names:
            if name != text:
                name2 += [name]
        self.names = name2
        text2 = ""
        for name in self.names:
            text2 += name + "\n"
        self.textBrowser.setText(text2)
        for t in self.update.model.threads:
            if t.name not in self.names:
                self.update.model.threads.remove(t)

    def closeEvent(self, event):
        self.queue.put(False)


def main():
    app = QtGui.QApplication(sys.argv)
    form = View()
    form.show()
    app.exec_()

if __name__ == '__main__':
    main()
