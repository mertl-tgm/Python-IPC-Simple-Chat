from PySide import QtGui
from PySide.QtCore import QThread, SIGNAL
from abc import ABCMeta, abstractmethod
import sys
import ClientView
import threading
import queue
import socket


class Update(QThread):
    """
        @author Ertl Marvin
        @version 2016-12-07

        This class inherits from the QThread, in the run method the queue will deliver the message, which got send
        from the client, these message will be send via signal to the gui

            :ivar queue:    The queue, from which the gui will get the received messages
    """

    def __init__(self, queue):
        """
        Initial the base class QThread and and set queue to the parameter queue
        :param queue: The queue, which will deliver the message
        """
        QThread.__init__(self)
        self.queue = queue

    def run(self):
        """
        Will run till the queue gets False, the queue will deliver the received message and send via a signal the text
        to the gui
        :return: None
        """
        while True:
            text = self.queue.get()
            if text is False:
                break
            self.emit(SIGNAL('add_post(QString)'), text)

    def message(self, text, title):
        """
        Will send the text and title to the gui, which will display a critical message with the title and the error
        :param text: The text of the message
        :param title: The title of the message
        :return: None
        """
        self.emit(SIGNAL('message(QString, QString)'), text, title)


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
    """
        @author Ertl Marvin
        @version 2016-12-07

        This class inherits from the threading.Thread and from Stoppable, this class will send the messages to the
        server and handle a thread, which receives the messages from the server

            :ivar port:     The port on which the client connect to the server
            :ivar host:     The ip on which the client connect to the server
            :ivar queue:    The queue from which the send method will get the message for sending
            :ivar con:      Connection to the server
            :ivar update:   Update object which send the signals to the gui, to change the gui
            :ivar queueR:   The queueR in which the recv class but the messages for the gui to display
            :ivar recv:     Recv is the class, which will receive the messages from the
            :ivar running:  Running says, if the run method is running or not
    """

    def __init__(self, queue, queueR, update):
        """
        Initial the base class threading.Thread and Stoppable, will set the attributes
        :param queue:   Queue for the sending messages
        :param queueR:  QueueR is the queue for the received messages
        :param update:  The update class is for changing the gui
        """
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
        """
        The method will connect to the server and then run in a loop for sending the messages to the server, this
        method will also start a class for receiving the messages from the server, if the run method could connect to
        the server, if not the client will display a cortical message and then shutdown the client
        :return: None
        """
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
        """
        The method will set running to False, which breaks the loop in the run method, it also puts a False to the queue
        in case, that the method will wait at the queue for a input and close the connection to the server, this will
        case a error in the reciv class.
        The method will also call stopping in the recv class
        :return: None
        """
        self.running = False
        self.queue.put(False)
        self.con.close()
        if self.recv is not None:
            self.recv.stopping()


class Recv(threading.Thread, Stoppable):
    """
        @author Ertl Marvin
        @version 2016-12-07

        This class inherits from the threading.Thread and from Stoppable, this class will receive the messages from the
        server put these messages in the queue for the gui to display these messages

            :ivar port:     The port on which the client connect to the server
            :ivar host:     The ip on which the client connect to the server
            :ivar con:      Connection to the server
            :ivar update:   Update object which send the signals to the gui, to change the gui
            :ivar queueR:   The queueR in which the recv class but the messages for the gui to display
            :ivar send:     Send is the class, which will get the send the messages to the server
            :ivar running:  Running says, if the run method is running or not
    """

    def __init__(self, queueR, update, con, send):
        """
        Initial the base class threading.Thread and Stoppable, will set the attributes
        :param queueR:  QueueR is the queue for the received messages
        :param update:  Reference to the update class, to change the gui
        :param con:     Connection to the server
        :param send:    Reference to the send class
        """
        threading.Thread.__init__(self)
        self.port = 4242
        self.host = "localhost"
        self.queue = queueR
        self.con = con
        self.update = update
        self.send = send
        self.running = True

    def run(self):
        """
        The method listen to the server for receiving messages, these messages will be put in the queue and the
        update thread will send a signal to the gui, to change the gui
        :return: None
        """
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
        """
        Set running to false and calls the stopping method in the send class
        :return: None
        """
        self.running = False
        if self.send.running is True:
            self.send.stopping()


class View(QtGui.QMainWindow, ClientView.Ui_MainWindow):
    """
        @author Ertl Marvin
        @version 2016-12-07

        This class inherits from the QtGui.QMainWindow and from ClientView.Ui_MainWindow,
        this class will setup the view and connection and will wait for signal to change the gui

            :ivar queueR:       The queue in which the received messages will be put
            :ivar update:       Class update, which send the signal to the view
            :ivar sendQ:        Queue for the sending messages
            :ivar send:         Class send will send the messages and handel the receive thread
    """

    def __init__(self):
        """
        Initial the base class threading.Thread, set up the Ui, create the queues for the classes and connect the method
        to the signal receiver, it will also start the update thread for updating the gui and the send thread for
        sending the messages to the server
        """
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
        """
        Read the text out of the input field and send it to the send class through the queue and clear the input line
        :return: None
        """
        text = self.lineEdit.text()
        self.sendQ.put(text)
        self.lineEdit.setText("")

    def add_post(self, text):
        """
        Append the received text to the textBrowser
        :param text: The received text from the client
        :return: None
        """
        self.textBrowser.append(str(text))

    def message(self, text, title):
        """
        Display a critical message with the given text and title and closes the gui
        :param text: Text for the message
        :param title: Title for the message
        :return: None
        """
        QtGui.QMessageBox.critical(self, title, text)
        self.close()

    def closeEvent(self, event):
        """
        Override the close event, puts a False to the receive queue to stop the threads and calls the stopping from the
        send class
        :param event: event which get calls from clicking on the exit button
        :return: None
        """
        self.queueR.put(False)
        self.send.stopping()


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
