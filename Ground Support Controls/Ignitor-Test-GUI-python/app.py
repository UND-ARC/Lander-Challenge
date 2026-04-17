import sys, os
from PyQt6 import QtCore, QtWidgets
from LabJackWorker import LabJackWorker
#from PyQt6 import uic
from MainWindow import Ui_MainWindow
from GraphWindow import GraphWindow
import math, time



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
        time.sleep(3)

        self.GraphWindow = GraphWindow()
        self.actionGraphWindow.triggered.connect(self.toggle_dashboard)

        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.labjack_signals.connect(self.displayLabjackValues)

        self.thread.start()
        #time.sleep(5)

        # Initialize the timers
        self.testTimerProgressBar = QtCore.QTimer()
        self.testTimerProgressBar.timeout.connect(self.update_progressBar)

        self.testTimer = QtCore.QTimer()
        self.testTimer.timeout.connect(self.endTest)


        self.testTimerCH4Delay = QtCore.QTimer()
        self.testTimerCH4Delay.timeout.connect(self.CH4DelayTimeout)

        self.testTimerSparkDelay = QtCore.QTimer()
        self.testTimerSparkDelay.timeout.connect(self.sparkDelayTimeout)

        self.sparkTimer = QtCore.QTimer()
        self.sparkTimer.timeout.connect(self.toggleSparkRelay)
        self.sparkRelayOn = False

        # Track our current position
        self.current_step = 0
        self.total_steps = 0

        # Connect the buttons
        self.StartTest.clicked.connect(self.start_test)


        self.ManOverride.clicked.connect(self.manOverride)
        self.manOverride(False)
        self.ManSpark.clicked.connect(self.manSpark)
        self.manSpark(False)
        self.ManPurgeBoth.clicked.connect(self.manPurgeBoth)
        self.manPurgeBoth(False)
        self.ManPurgeGOX.clicked.connect(self.manPurgeGOX)
        self.manPurgeGOX(False)
        self.ManPurgeCH4.clicked.connect(self.manPurgeCH4)
        self.manPurgeCH4(False)
        self.ManGOXValve.clicked.connect(self.manGOXValve)
        self.manGOXValve(False)
        self.ManCH4Valve.clicked.connect(self.manCH4Valve)
        self.manCH4Valve(False)



        self.setLoggingEnabled(False)
        self.DataLogging.clicked.connect(self.setLoggingEnabled)

        self.ESTOP.clicked.connect(self.eStop)
        self.KillIgnitor.clicked.connect(self.killIgnitor)



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

    def manOverride(self, checked):
        if checked:
            self.ManSpark.setEnabled(True)
            self.ManPurgeBoth.setEnabled(True)
            self.ManPurgeGOX.setEnabled(True)
            self.ManPurgeCH4.setEnabled(True)
            self.ManGOXValve.setEnabled(True)
            self.ManCH4Valve.setEnabled(True)

        else:
            self.ManSpark.setEnabled(False)
            self.ManPurgeBoth.setEnabled(False)
            self.ManPurgeGOX.setEnabled(False)
            self.ManPurgeCH4.setEnabled(False)
            self.ManGOXValve.setEnabled(False)
            self.ManCH4Valve.setEnabled(False)

    def manSpark(self, checked):
        if checked:
            self.startFireSparkPlug()

        else:
            self.stopFireSparkPlug()

    def manPurgeBoth(self, checked):
        if checked:
            self.openBothNitrogenValves()
        else:
            self.closeBothNitrogenValves()

    def manPurgeGOX(self, checked):
        if checked:
            self.openNitrogenValveGOX()
        else:
            self.closeNitrogenValveGOX()

    def manPurgeCH4(self, checked):
        if checked:
            self.openNitrogenValveCH4()
        else:
            self.closeNitrogenValveCH4()

    def manGOXValve(self, checked):
        if checked:
            self.openGOXValve()
        else:
            self.closeGOXValve()

    def manCH4Valve(self, checked):
        if checked:
            self.openCH4Valve()

        else:
            self.closeCH4Valve()


    def eStop(self, checked):
        if checked:
            print("Emergency Stop!")
            self.closeCH4Valve()
            self.closeGOXValve()
            self.stopFireSparkPlug()
            self.openBothNitrogenValves()

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
        self.ManGOXValve.setText("OPEN")
        self.ManGOXValve.setStyleSheet("background-color: #2ecc71; color: black; font-weight: bold;") #green
        self.worker.write_value("FIO3", 1)

    def closeGOXValve(self):
        print("Closing GOX Valve!")
        self.ManGOXValve.setText("CLOSE")
        self.ManGOXValve.setStyleSheet("background-color: red; color: white; border-radius: 5px;")
        self.worker.write_value("FIO3", 0)

    def openCH4Valve(self):
        if self.ESTOP.isChecked():
            return  # if estop is on we don't want fire
        print("Opening CH4 Valve!")
        self.ManCH4Valve.setText("OPEN")
        self.ManCH4Valve.setStyleSheet("background-color: #2ecc71; color: black; font-weight: bold;") #green
        self.worker.write_value("FIO4", 1)

    def closeCH4Valve(self):
        print("Closing CH4 Valve!")
        self.ManCH4Valve.setText("CLOSE")
        self.ManCH4Valve.setStyleSheet("background-color: red; color: white; border-radius: 5px;")
        self.worker.write_value("FIO4", 0)

    def openBothNitrogenValves(self):
        print("Opening Both Nitrogen Valves!")
        self.ManPurgeBoth.setText("OPEN")
        self.ManPurgeBoth.setStyleSheet("background-color: #2ecc71; color: black; font-weight: bold;") #green
        self.openNitrogenValveGOX()
        self.openNitrogenValveCH4()

    def closeBothNitrogenValves(self):
        print("Closing Both Nitrogen Valves!")
        self.ManPurgeBoth.setText("CLOSED")
        self.ManPurgeBoth.setStyleSheet("background-color: red; color: white; border-radius: 5px;")
        self.closeNitrogenValveGOX()
        self.closeNitrogenValveCH4()

    def openNitrogenValveGOX(self):
        print("Opening Nitrogen Valve GOX!")
        self.ManPurgeGOX.setText("OPEN")
        self.ManPurgeGOX.setStyleSheet("background-color: #2ecc71; color: black; font-weight: bold;")  # green
        self.worker.write_value("FIO1", 1)


    def closeNitrogenValveGOX(self):
        print("Closing Nitrogen Valve GOX!")
        self.ManPurgeGOX.setText("CLOSE")
        self.ManPurgeGOX.setStyleSheet("background-color: red; color: white; border-radius: 5px;")
        self.worker.write_value("FIO1", 0)

    def openNitrogenValveCH4(self):
        print("Opening Nitrogen Valve Ch4!")
        self.ManPurgeCH4.setText("OPEN")
        self.ManPurgeCH4.setStyleSheet("background-color: #2ecc71; color: black; font-weight: bold;")  # green
        self.worker.write_value("FIO2", 1)


    def closeNitrogenValveCH4(self):
        print("Closing Nitrogen Valve CH4!")
        self.ManPurgeCH4.setText("CLOSE")
        self.ManPurgeCH4.setStyleSheet("background-color: red; color: white; border-radius: 5px;")
        self.worker.write_value("FIO2", 0)


    def startFireSparkPlug(self):
        if self.ESTOP.isChecked() or self.KillIgnitor.isChecked():
            return #if estop is on we don't want fire
        print("Start Fire Spark Plug!")
        self.ManSpark.setText("ON")
        self.ManSpark.setStyleSheet("background-color: #2ecc71; color: black; font-weight: bold;")  # green
        self.worker.write_value("FIO6", 1)
        self.sparkTimer.start(333)


    def stopFireSparkPlug(self):
        print("Stopped Fire Spark Plug!")
        self.ManSpark.setText("OFF")
        self.ManSpark.setStyleSheet("background-color: red; color: white; border-radius: 5px;")

        self.sparkTimer.stop()
        self.worker.write_value("FIO6", 0)
        self.worker.write_value("FIO5", 0)

    def toggleSparkRelay(self):
        if self.sparkRelayOn:
            self.worker.write_value("FIO5", 0)
        else:
            self.worker.write_value("FIO5", 1)

    def displayLabjackValues(self, values):
        try:
            # Format to 2 decimal place
            self.PT_00.setText(f'{values["PT-00"]:.2f} psi')
            self.PT_01.setText(f'{values["PT-01"]:.2f} psi')
            self.PT_02.setText(f'{values["PT-02"]:.2f} psi')
            self.PT_03.setText(f'{values["PT-03"]:.2f} psi')
            self.PT_04.setText(f'{values["PT-04"]:.2f} psi')
            self.PT_05.setText(f'{values["PT-05"]:.2f} psi')
            self.PT_06.setText(f'{values["PT-06"]:.2f} psi')
            self.PT_07.setText(f'{values["PT-07"]:.2f} psi')
            self.PT_08.setText(f'{values["PT-08"]:.2f} psi')
            self.PT_09.setText(f'{values["PT-09"]:.2f} psi')
            self.PT_10.setText(f'{values["PT-10"]:.2f} psi')
            self.PT_11.setText(f'{values["PT-11"]:.2f} psi')
            self.PT_12.setText(f'{values["PT-12"]:.2f} psi')

            self.TC_15.setText(f'{values["TC-15"]:.2f} °C')
            self.TC_16.setText(f'{values["TC-16"]:.2f} °C')
            self.TC_17.setText(f'{values["TC-17"]:.2f} °C')
            self.TC_18.setText(f'{values["TC-18"]:.2f} °C')
            self.TC_19.setText(f'{values["TC-19"]:.2f} °C')




            GOXMassFlowRate, GOXFlowChoked = calculate_flow(values["PT-01"], values["PT-02"], values["TC-15"], "O2")

            self.MdotGOX.setText(f'{GOXMassFlowRate:.2f} km/h')
            if GOXFlowChoked:
                self.MdotGOX.setStyleSheet("background-color: blue; color: white;")
            else:
                self.MdotGOX.setStyleSheet("background-color: yellow; color: black;")

            CH4MassFlowRate, CH4FlowChoked = calculate_flow(values["PT-05"], values["PT-06"], values["TC-17"], "CH4")

            self.MdotCH4.setText(f'{CH4MassFlowRate:.2f} km/h')
            if CH4FlowChoked:
                self.MdotCH4.setStyleSheet("background-color: blue; color: white;")
            else:
                self.MdotCH4.setStyleSheet("background-color: yellow; color: black;")

            upperAlertPressure = 10000
            lowerAlertPressure = 10
            if (values["PT-03"] > upperAlertPressure) or (values["PT-03"] < lowerAlertPressure) or (values["PT-04"] > upperAlertPressure) or (values["PT-04"] < lowerAlertPressure):

                self.PressureAlarm.setCurrentWidget(self.Alarm)
                self.PressureAlarm.show()
            else:
                self.PressureAlarm.setCurrentWidget(self.Normal)
                self.PressureAlarm.show()

            if self.PressureAlarm.currentWidget() == self.Normal and not (self.ESTOP.isChecked() or self.KillIgnitor.isChecked()):
                self.TestStatus.setCurrentWidget(self.GO)
                self.TestStatus.show()
                self.StartTest.setEnabled(True)
            else:
                self.TestStatus.setCurrentWidget(self.NOGO)
                self.TestStatus.show()
                self.StartTest.setEnabled(False)

            #Graphs
            # Add new value to the right of the deque (automatically pushes old ones out)
            self.GraphWindow.ChamberPressureGraph.updateGraph(values["PT-05"])
            self.GraphWindow.GOXMassFlowRateGraph.updateGraph(GOXMassFlowRate)
            self.GraphWindow.CH4MassFlowRateGraph.updateGraph(CH4MassFlowRate)

        except Exception as e:
            print(f"LabJack Error: {e}")

    def toggle_dashboard(self):
        if self.GraphWindow.isVisible():
            self.GraphWindow.activateWindow()  # Bring to front if already open
            self.GraphWindow.raise_()
        else:
            self.GraphWindow.show()





    def handle_error(self, err_msg):
        """Handle LabJack Error"""
        print(f"LabJack Error: {err_msg}")

    def closeEvent(self, event):
        self.GraphWindow.close()  # Close the separate window
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()
        event.accept()


def calculate_flow(P1_psi, P2_psi, T1_C, Cv, gas_type='O2'):
    #TODO constants
    c_d = 0.8
    A = -1
    y = -1
    R = -1
    T = T1_C + 273.15
    if gas_type == 'O2':
        y = 1.4
        A = 0.03125
        R = 259.8 # kg / (m*s^2)
    elif gas_type == 'CH4':
        y = 1.3
        A = 0.03125
        R = 519.6 # kg / (m*s^2)

    choked = True

    if choked:
        #for choked flow
        m_dot = c_d * A * P1_psi * math.sqrt(y/(R*T))*math.pow(2/(y+1),(y+1)/(2*(y-1)))

    else:
        m_dot = 1

    return m_dot, choked





if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()