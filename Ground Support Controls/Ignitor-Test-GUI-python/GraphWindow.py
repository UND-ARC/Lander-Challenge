import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore, QtGui
from collections import deque


class GraphWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Engine Test Dashboard")
        self.resize(1000, 700)
        self.setStyleSheet("background-color: #121212; color: white;")

        # 1. Use QGridLayout
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)


        #graphs
        self.ChamberPressureGraph = Graph("Chamber Pressure", "Chamber Pressure (psi)", "Time")
        self.GOXMassFlowRateGraph = Graph("GOX mass flow rate", "mass flow rate (kg/s)", "Time")
        self.CH4MassFlowRateGraph = Graph("CH4 mass flow rate", "mass flow rate (kg/s)", "Time")



        # Add to grid: (widget, row, col, rowSpan, colSpan)
        self.layout.addWidget(self.ChamberPressureGraph, 0, 0)
        self.layout.addWidget(self.GOXMassFlowRateGraph, 1, 0)
        self.layout.addWidget(self.CH4MassFlowRateGraph, 1, 1)


class Graph(QtWidgets.QWidget):
    def __init__(self, title, yLabel, xLabel="Time"):
        super().__init__()
        self.title = title
        self.yLabel = yLabel
        self.xLabel = xLabel

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.max_points = 200
        self.xAxis = list(range(self.max_points))

        self.label = QtWidgets.QLabel(title)
        self.label.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Weight.Bold))
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.GraphWidget = pg.PlotWidget()
        self.data = deque([0.0] * self.max_points, maxlen=self.max_points)
        self.curve = self.GraphWidget.plot(self.xAxis, list(self.data), pen=pg.mkPen('y', width=2))
        self.GraphWidget.setLabel('left', yLabel)
        self.GraphWidget.setLabel('bottom', xLabel)

        # Add to internal vertical layout
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.GraphWidget)

    @QtCore.pyqtSlot(float)
    def updateGraph(self, val):
        self.data.append(val)
        self.curve.setData(self.xAxis, list(self.data))


