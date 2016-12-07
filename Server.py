from PySide import QtGui
from PySide.QtCore import QThread, SIGNAL
from abc import ABCMeta, abstractmethod
import sys
import ServerView
import threading
import queue
import socket


class Update(QThread):
    """
        @author Ertl Marvin
        @version 2016-12-07

        This class inherits from the QThread, the model will be started and handel the receive, send and listen thread,
        this class will send the signal to the view, to change the gui

            :ivar queue:    The queue for the received messages
            :ivar model:    Model which handles the receive, send and listen thread
    """

    def __init__(self, queue):
        """
        Initial the base class QThread and create Model
        :param queue: The queue for the receiving messages
        """
        QThread.__init__(self)
        self.queue = queue
        self.model = Model(self.queue, self)

    def run(self):
        """
        The run method start the model and get the received messages to send a signal to change the gui
        :return: None
        """
        self.model.start()
        while True:
            text = self.queue.get()
            if text is False:
                break
            self.emit(SIGNAL('add_post(QString)'), text)
        self.model.stopping()
        self.model.join()

    def send(self, text):
        """
        Will send the text via the model to all clients
        :param text: The text which the server received from one client and will be send ot all clients
        :return: None
        """
        self.model.send(text)

    def set_client(self, text):
        """
        Send a signal to the view to add the text to the connected clients text field
        :param text: The client name which will be added to the list in the view
        :return: None
        """
        self.emit(SIGNAL('set_client(QString)'), text)

    def remove_client(self, text):
        """
        Will send a signal to the view to remove one of the client names from the gui
        :param text: The client name which will be removed from the list
        :return: None
        """
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
    """
        @author Ertl Marvin
        @version 2016-12-07

        This class inherits from threading.Thread and Stoppable, the class will listen for client, which try to connect
        to the server and handel the threads, receiving form these threads and sending messages to these threads.

            :ivar port:             The port on which the socket listen for clients
            :ivar threads:          List of all connected threads to the server
            :ivar queue:            The queue for the received messages
            :ivar update:           Class for updating the gui
            :ivar running:          Set if the run methode will listen for threads
            :ivar serversocket:     The serversocket on which the server listen for clients
    """

    def __init__(self, queue, update):
        """
        Initial the base class threading.Thread and Stoppable, also setup the port to 4242, running to true and all
        other variables to the default value
        :param queue: The queue for the receiving messages
        :param update: Update class for making changes in the gui
        """
        threading.Thread.__init__(self)
        self.port = 4242
        self.threads = []
        self.queue = queue
        self.update = update
        self.running = True
        self.serversocket = None

    def run(self):
        """
        The run methode will create a socket and listen for clients, if a client connects to the server, the client will
        be added to the list threads and the server starts to recv messages from these connections, if the server
        shuts down, the socket will be closed and all threads for the clients will be stopped.
        :return: None
        """
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
        """
        Send the text messages to all clients. which are connect to the server
        :param text:
        :return:
        """
        for t in self.threads:
            t.send(text)

    def stopping(self):
        """
        Sets running to False, which stops the loop in the run method and closes the serversocket.
        :return: None
        """
        self.running = False
        self.serversocket.close()


class Recv(threading.Thread, Stoppable):
    """
        @author Ertl Marvin
        @version 2016-12-07

        This class inherits from threading.Thread and Stoppable, the class will wait to receive messages from the
        client, these messages will be put into the queue, so that it can be displayed by the update class

            :ivar running:          Set if the run methode will listen for threads
            .ivar con:              Connection to the thread
            :ivar queue:            The queue for the received messages
            :ivar name:             Name of the client
            :ivar update:           Class for updating the gui
    """

    def __init__(self, con, queue, name, update):
        """
        Initial the threading.Thread class, set running to true and set the attributes to the given values
        :param con: The connection to the thread
        :param queue: The queue for the received messages
        :param name: The name of the thread
        :param update: Class update to make changes to the gui
        """
        threading.Thread.__init__(self)
        self.running = True
        self.con = con
        self.queue = queue
        self.name = name
        self.update = update

    def stopping(self):
        """
        Will set running to false, loop in run method will stop
        :return: None
        """
        self.running = False

    def run(self):
        """
        Waits to get a messages from the client until running is False or the connections will be closed, if a messages
        is received it wiil be put into the queue, so that the update class can display it in the gui, if the connection
        is closed the name of the client will be removed from the connected clients list
        :return: None
        """
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
        """
        Sends the message to the client
        :param text: The message, which will be sent do the client
        :return: None
        """
        self.con.send(text.encode())


class View(QtGui.QMainWindow, ServerView.Ui_MainWindow):
    """
        @author Ertl Marvin
        @version 2016-12-07

        This class inherits from the QtGui.QMainWindow and from ServerView.Ui_MainWindow,
        this class will setup the view and connection and will wait for a client to connect to

            :ivar queue:        The queue in which the received messages will be put
            :ivar update:       Class update, which send the signal to the view
            :ivar names:        List of the names of the connected clients
    """

    def __init__(self):
        """
        Initial the base class threading.Thread, set up the Ui, create the queues for the classes and connect the method
        to the signal receiver, it will also start the update thread for updating the gui and will wait for a client
        to connect to the serversocket
        """
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
        """
        Adds the received message to the text field in the gui
        :param text: The messages which will be added
        :return: None
        """
        self.textBrowser_2.append(str(text))
        self.update.send(text)

    def set_client(self, text):
        """
        Adds the name of the client to the connect clients field
        :param text: The name of the client
        :return: None
        """
        self.textBrowser.append(str(text))
        self.names += [text]

    def remove_client(self, text):
        """
        Removes the name of the disconnected client from the name list and also remove it from the gui
        :param text: The name of the client which should be removed
        :return: None
        """
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
        """
        Overwritten closeEvent, will be called if the user exit the program, will put a False into the queue to stop all
        threads and exit the program correctly
        :param event:
        :return:
        """
        self.queue.put(False)


def main():
    """
    Setups the app and view and display it
    :return: None
    """
    app = QtGui.QApplication(sys.argv)
    form = View()
    form.show()
    app.exec_()

if __name__ == '__main__':
    main()
