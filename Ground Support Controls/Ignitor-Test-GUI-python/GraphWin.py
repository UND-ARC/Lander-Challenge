import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore, QtGui
from collections import deque


class GraphWin(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Engine Test Dashboard")
        self.resize(1000, 700)
        self.setStyleSheet("background-color: #121212; color: white;")

        # 1. Use QGridLayout
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

        # 2. Setup Plot Data
        self.max_points = 200
        self.x_axis = list(range(self.max_points))

        # 3. Create CH4 Section (Row 0)
        self.ch4_label = QtWidgets.QLabel("METHANE TEMPERATURE (CH4)")
        self.ch4_label.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Weight.Bold))
        self.ch4_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.ch4_graph = pg.PlotWidget()
        self.ch4_data = deque([0.0] * self.max_points, maxlen=self.max_points)
        self.ch4_curve = self.ch4_graph.plot(self.x_axis, list(self.ch4_data), pen=pg.mkPen('y', width=2))

        # Add to grid: (widget, row, col, rowSpan, colSpan)
        self.layout.addWidget(self.ch4_label, 0, 0)
        self.layout.addWidget(self.ch4_graph, 1, 0)

        # 4. Create GOX Section (Row 0, Column 1)
        self.gox_label = QtWidgets.QLabel("OXYGEN TEMPERATURE (GOX)")
        self.gox_label.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Weight.Bold))
        self.gox_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.gox_graph = pg.PlotWidget()
        self.gox_data = deque([0.0] * self.max_points, maxlen=self.max_points)
        self.gox_curve = self.gox_graph.plot(self.x_axis, list(self.gox_data), pen=pg.mkPen('r', width=2))

        self.layout.addWidget(self.gox_label, 0, 1)
        self.layout.addWidget(self.gox_graph, 1, 1)

    @QtCore.pyqtSlot(float)
    def update_ch4(self, val):
        self.ch4_data.append(val)
        self.ch4_curve.setData(self.x_axis, list(self.ch4_data))

    @QtCore.pyqtSlot(float)
    def update_gox(self, val):
        self.gox_data.append(val)
        self.gox_curve.setData(self.x_axis, list(self.gox_data))