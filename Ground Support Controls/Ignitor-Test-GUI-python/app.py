import sys
from PyQt6 import QtCore, QtGui, QtWidgets

from LabJackWorker import LabJackWorker
#from PyQt6 import uic
from MainWindow import Ui_MainWindow
from labjack import ljm


#run to covert .ui file to python
#pyuic6 mainwindow.ui -o MainWindow.py

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        #uic.loadUi("mainwindow.ui", self)
        self.setupUi(self)

        #start all valves closed
        self.closeCH4Valve()
        self.closeGOXValve()
        self.stopFireSparkPlug()
        self.closeNitrogenValve()

        #LabJack data
        self.thread = QtCore.QThread()
        handle = None
        try:
            handle = ljm.openS("T7", "ANY", "ANY")
        except Exception as e:
            print(e)

        self.worker = LabJackWorker(handle)
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.run)
        #self.worker.voltage_received.connect(self.update_lcd)
        self.worker.error_occurred.connect(self.handle_error)

        self.thread.start()

        # Initialize the timers
        self.testTimerProgressBar = QtCore.QTimer()
        self.testTimerProgressBar.timeout.connect(self.update_progressBar)

        self.testTimer = QtCore.QTimer()
        self.testTimer.timeout.connect(self.endTest)


        self.testTimerCH4Delay = QtCore.QTimer()
        self.testTimerCH4Delay.timeout.connect(self.CH4DelayTimeout)

        self.testTimerSparkDelay = QtCore.QTimer()
        self.testTimerSparkDelay.timeout.connect(self.SparkDelayTimeout)

        # Track our current position
        self.current_step = 0
        self.total_steps = 0

        # Connect the button
        self.StartTest.clicked.connect(self.start_test)

        self.NitrogenPurge.clicked.connect(self.nitrogenPurgeClicked)
        self.DataLogging.clicked.connect(self.DataLogging)



    def start_test(self):
        #progress bar
        # 1. Get duration in seconds from spinbox
        duration = self.FiringDurationSeconds.value()

        if duration <= 0:
            return

        # 2. Setup the progress tracking
        # We will update every 100ms for a smooth look
        # Total steps = duration * 10 (since 10 * 100ms = 1 second)
        self.current_step = 0
        self.total_steps = duration * 10

        self.TestProgress.setMaximum(int(self.total_steps))
        self.TestProgress.setValue(0)

        # 3. Disable the button so they can't spam it
        self.StartTest.setEnabled(False)

        # 4. Start the timer (100ms interval)
        self.testTimerProgressBar.start(100)

        self.testTimer.start(int(duration * 1000))
        print("Starting Test!")

        #GOX no delay
        self.openGOXValve()

        #CH4
        CH4Delay = self.CH4DelaySeconds.value()

        self.testTimerCH4Delay.start(int(CH4Delay*1000))

        #Spark
        sparkDelay = self.SparkDelaySeconds.value() + CH4Delay

        self.testTimerSparkDelay.start(int(sparkDelay*1000))



    def update_progressBar(self):
        self.current_step += 1
        self.TestProgress.setValue(self.current_step)

        timeRemainingSec = (self.total_steps - self.current_step)/10
        self.TimeRemaining.display(timeRemainingSec)

        # Check if we are finished
        if self.current_step >= self.total_steps:
            self.TimeRemaining.display(timeRemainingSec)
            self.testTimerProgressBar.stop()
            #self.TestProgress.setValue(0)

    def CH4DelayTimeout(self):
        self.testTimerCH4Delay.stop()
        self.openCH4Valve()

    def SparkDelayTimeout(self):
        self.testTimerSparkDelay.stop()
        self.startFireSparkPlug()

    def endTest(self):
        self.testTimer.stop()
        print("Ending Test!")
        self.StartTest.setEnabled(True)
        self.closeCH4Valve()
        self.closeGOXValve()
        self.stopFireSparkPlug()

    def setLoggingEnabled(self, checked):
        if checked:
            self.DataLogging.setText("ON")
            self.worker.setLoggingEnabled(True)
        else:
            self.DataLogging.setText("OFF")
            self.worker.setLoggingEnabled(False)


    def openGOXValve(self):
        print("Opening GOX Valve!")
        self.GOXValveIndicator.setCurrentWidget(self.GOX_Open)
        self.GOXValveIndicator.show()
        #TODO

    def closeGOXValve(self):
        print("Closing GOX Valve!")
        self.GOXValveIndicator.setCurrentWidget(self.GOX_Closed)
        self.GOXValveIndicator.show()
        #TODO

    def openCH4Valve(self):
        print("Opening CH4 Valve!")
        self.CH4ValveIndicator.setCurrentWidget(self.CH4_Open)
        self.CH4ValveIndicator.show()
        #TODO

    def closeCH4Valve(self):
        print("Closing CH4 Valve!")
        self.CH4ValveIndicator.setCurrentWidget(self.CH4_Closed)
        self.CH4ValveIndicator.show()
        #TODO

    def nitrogenPurgeClicked(self, checked):
        if checked:
            self.NitrogenPurge.setText("ON")
            self.openNitrogenValve()
        else:
            self.NitrogenPurge.setText("OFF")
            self.closeNitrogenValve()

    def openNitrogenValve(self):
        print("Opening Nitrogen Valve!")
        self.worker.write_value("FIO7", 1)

    def closeNitrogenValve(self):
        print("Closing Nitrogen Valve!")
        self.worker.write_value("FIO7", 0)


    def startFireSparkPlug(self):
        print("Start Fire Spark Plug!")
        self.IgnitorIndicator.setCurrentWidget(self.Ignitor_On)
        self.IgnitorIndicator.show()
        #TODO

    def stopFireSparkPlug(self):
        print("Stopped Fire Spark Plug!")
        self.IgnitorIndicator.setCurrentWidget(self.Ignitor_Off)
        self.IgnitorIndicator.show()
        #TODO

    '''Handle LabJack Error'''
    def handle_error(self, err_msg):
        print(f"LabJack Error: {err_msg}")




if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()