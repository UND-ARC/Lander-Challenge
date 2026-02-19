import sys
from PyQt6 import QtCore, QtGui, QtWidgets
#from PyQt6 import uic
from MainWindow import Ui_MainWindow

#pyuic6 mainwindow.ui -o MainWindow.py

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        #uic.loadUi("mainwindow.ui", self)
        self.setupUi(self)



        # Initialize a timer
        self.testTimer = QtCore.QTimer()
        self.testTimer.timeout.connect(self.update_progress)

        # Track our current position
        self.current_step = 0
        self.total_steps = 0

        # Connect the button
        self.StartTest.clicked.connect(self.start_test)

    def start_test(self):
        # 1. Get duration in seconds from spinbox
        duration = self.FiringDurationSeconds.value()

        if duration == 0:
            return

        # 2. Setup the progress tracking
        # We will update every 100ms for a smooth look
        # Total steps = duration * 10 (since 10 * 100ms = 1 second)
        self.current_step = 0
        self.total_steps = duration * 10

        self.TestProgress.setMaximum(self.total_steps)
        self.TestProgress.setValue(0)

        # 3. Disable the button so they can't spam it
        self.StartTest.setEnabled(False)

        # 4. Start the timer (100ms interval)
        self.testTimer.start(100)

    def update_progress(self):
        self.current_step += 1
        self.TestProgress.setValue(self.current_step)

        # Check if we are finished
        if self.current_step >= self.total_steps:
            self.testTimer.stop()
            self.StartTest.setEnabled(True)
            #self.TestProgress.setValue(0)
            print("Test Complete!")
            


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()