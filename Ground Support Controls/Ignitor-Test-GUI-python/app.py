import sys
from PyQt6 import QtCore, QtWidgets

from LabJackWorker import LabJackWorker
#from PyQt6 import uic
from MainWindow import Ui_MainWindow


#run to covert .ui file to python
#pyuic6 mainwindow.ui -o MainWindow.py

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        #uic.loadUi("mainwindow.ui", self)
        self.setupUi(self)

        #LabJack data
        self.thread = QtCore.QThread()

        self.worker = LabJackWorker()
        self.worker.moveToThread(self.thread)



        # Connect signals
        self.thread.started.connect(self.worker.run)
        #self.worker.voltage_received.connect(self.update_lcd)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.labjack_signals.connect(self.displayLabjackValues)


        self.thread.start()

        # Initialize the timers
        self.testTimerProgressBar = QtCore.QTimer()
        self.testTimerProgressBar.timeout.connect(self.update_progressBar)

        self.testTimer = QtCore.QTimer()
        self.testTimer.timeout.connect(self.endTest)


        self.testTimerCH4Delay = QtCore.QTimer()
        self.testTimerCH4Delay.timeout.connect(self.CH4DelayTimeout)

        self.testTimerSparkDelay = QtCore.QTimer()
        self.testTimerSparkDelay.timeout.connect(self.sparkDelayTimeout)

        # Track our current position
        self.current_step = 0
        self.total_steps = 0

        # Connect the button
        self.StartTest.clicked.connect(self.start_test)

        self.NitrogenPurge.clicked.connect(self.nitrogenPurgeClicked)

        self.manualValveControl(False)
        self.ManualValveControl.clicked.connect(self.manualValveControl)

        self.GOX_Valve.clicked.connect(self.manualGOXControl)
        self.CH4_Valve.clicked.connect(self.manualCH4Control)

        self.manualIgnitionControl(False)
        self.ManualIgitionControl.clicked.connect(self.manualIgnitionControl)

        self.Ignitor.clicked.connect(self.manualSparkControl)

        self.setLoggingEnabled(False)
        self.DataLogging.clicked.connect(self.setLoggingEnabled)

        self.ESTOP.clicked.connect(self.eStop)
        self.KillIgnitor.clicked.connect(self.killIgnitor)

        # start all valves closed
        self.closeCH4Valve()
        self.closeGOXValve()
        self.stopFireSparkPlug()
        self.closeNitrogenValve()




    def start_test(self):
        #progress bar
        # 1. Get duration in seconds from spinbox
        duration = self.FiringDurationSeconds.value()

        if duration <= 0:
            return

        # 2. Set up the progress tracking
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

    def sparkDelayTimeout(self):
        self.testTimerSparkDelay.stop()
        self.startFireSparkPlug()

    def endTest(self):
        self.testTimer.stop()
        print("Ending Test!")
        self.StartTest.setEnabled(True)
        self.closeCH4Valve()
        self.closeGOXValve()
        self.stopFireSparkPlug()

    def manualValveControl(self, checked):
        if checked:
            self.ManualValveControl.setText("Manual")
            self.NitrogenPurge.setEnabled(True)
            self.GOX_Valve.setEnabled(True)
            self.CH4_Valve.setEnabled(True)

        else:
            self.ManualValveControl.setText("AUTO")
            self.NitrogenPurge.setEnabled(False)
            self.GOX_Valve.setEnabled(False)
            self.CH4_Valve.setEnabled(False)

    def manualIgnitionControl(self, checked):
        if checked:
            self.ManualIgitionControl.setText("Manual")
            self.Ignitor.setEnabled(True)

        else:
            self.ManualIgitionControl.setText("AUTO")
            self.Ignitor.setEnabled(False)

    def manualCH4Control(self, checked):
        if checked:
            self.openCH4Valve()

        else:
            self.closeCH4Valve()


    def manualGOXControl(self, checked):
        if checked:
            self.openGOXValve()
        else:
            self.closeGOXValve()


    def manualSparkControl(self, checked):
        if checked:
            self.startFireSparkPlug()

        else:
            self.stopFireSparkPlug()

    def eStop(self, checked):
        if checked:
            print("Emergency Stop!")
            self.closeCH4Valve()
            self.closeGOXValve()
            self.stopFireSparkPlug()
            #TODO do we want the nitrogen to open after a estop?
            # self.openNitrogenValve()

    def killIgnitor(self, checked):
        if checked:
            print("Killing Ignitor!")
            self.stopFireSparkPlug()



    def setLoggingEnabled(self, checked):
        if checked:
            self.DataLogging.setText("ON")
            self.worker.setLoggingEnabled(True)
        else:
            self.DataLogging.setText("OFF")
            self.worker.setLoggingEnabled(False)


    def openGOXValve(self):
        if self.ESTOP.isChecked():
            return #if estop is on we don't want fire
        print("Opening GOX Valve!")
        self.GOX_Valve.setText("OPEN")
        self.GOXValveIndicator.setCurrentWidget(self.GOX_Open)
        self.GOXValveIndicator.show()
        #TODO self.worker.write_value("FIO8", 1)

    def closeGOXValve(self):
        print("Closing GOX Valve!")
        self.GOX_Valve.setText("CLOSE")
        self.GOXValveIndicator.setCurrentWidget(self.GOX_Closed)
        self.GOXValveIndicator.show()
        #TODO self.worker.write_value("FIO8", 0)

    def openCH4Valve(self):
        if self.ESTOP.isChecked():
            return  # if estop is on we don't want fire
        print("Opening CH4 Valve!")
        self.CH4_Valve.setText("OPEN")
        self.CH4ValveIndicator.setCurrentWidget(self.CH4_Open)
        self.CH4ValveIndicator.show()
        #TODO self.worker.write_value("FIO9", 1)

    def closeCH4Valve(self):
        print("Closing CH4 Valve!")
        self.CH4_Valve.setText("CLOSE")
        self.CH4ValveIndicator.setCurrentWidget(self.CH4_Closed)
        self.CH4ValveIndicator.show()
        #TODO self.worker.write_value("FIO9", 0)

    def displayLabjackValues(self, values):
        # Format to 2 decimal place
        self.TC_01.setText(f'{values["CH4Temp"]:.2f} °C')
        self.TC_02.setText(f'{values["GOXTemp"]:.2f} °C')
        self.PT_01.setText(f'{values["PT-01"]:.2f} psi')
        self.PT_02.setText(f'{values["PT-02"]:.2f} psi')
        self.PT_03.setText(f'{values["PT-03"]:.2f} psi')
        self.PT_04.setText(f'{values["PT-04"]:.2f} psi')
        self.PT_05.setText(f'{values["PT-05"]:.2f} psi')
        self.PT_06.setText(f'{values["PT-06"]:.2f} psi')
        self.PT_07.setText(f'{values["PT-07"]:.2f} psi')


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
        if self.ESTOP.isChecked() or self.KillIgnitor.isChecked():
            return #if estop is on we don't want fire
        print("Start Fire Spark Plug!")
        self.Ignitor.setText("ON")
        self.IgnitorIndicator.setCurrentWidget(self.Ignitor_On)
        self.IgnitorIndicator.show()
        #TODO

    def stopFireSparkPlug(self):
        print("Stopped Fire Spark Plug!")
        self.Ignitor.setText("OFF")
        self.IgnitorIndicator.setCurrentWidget(self.Ignitor_Off)
        self.IgnitorIndicator.show()
        #TODO


    def handle_error(self, err_msg):
        """Handle LabJack Error"""
        print(f"LabJack Error: {err_msg}")




if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()