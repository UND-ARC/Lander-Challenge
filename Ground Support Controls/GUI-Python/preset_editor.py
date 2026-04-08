import json
from typing import Dict, Any, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QDialog, QDoubleSpinBox, QFileDialog, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget, QCheckBox, QStackedWidget
)

RELAY_CHANNELS = [
    {"key": f"D{i}", "label": f"Relay {i} (NO)" if i < 4 else f"Relay {i} (NC)"}
    for i in range(8)
]
ANALOG_CHANNELS = [f"A{i}" for i in range(2)]

# -------------------------
# Data helpers
# -------------------------

def default_preset():
    return {
        "version": 1,
        "steps": []
    }

def save_preset(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def load_preset(path):
    with open(path, "r") as f:
        return json.load(f)

# -------------------------
# Step Editor Dialog
# -------------------------

class StepDialog(QDialog):
    def __init__(self, parent, step=None):
        super().__init__(parent)
        self.setWindowTitle("Step")

        self.time = QDoubleSpinBox()
        self.time.setRange(0, 1e6)
        self.time.setSuffix(" s")

        self.digs = {}
        dig_box = QGroupBox("Digital")
        dig_layout = QHBoxLayout()

        for ch in RELAY_CHANNELS:
            cb = QCheckBox(ch["label"])
            self.digs[ch["key"]] = cb
            dig_layout.addWidget(cb)

        dig_box.setLayout(dig_layout)

        self.anas = {}
        ana_box = QGroupBox("Analog (%)")
        ana_layout = QHBoxLayout()

        for ch in ANALOG_CHANNELS:
            sp = QDoubleSpinBox()
            sp.setRange(0, 100)
            sp.setSuffix("%")
            self.anas[ch] = sp
            ana_layout.addWidget(sp)

        ana_box.setLayout(ana_layout)

        form = QFormLayout()
        form.addRow("Time:", self.time)

        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(dig_box)
        layout.addWidget(ana_box)
        layout.addWidget(ok)

        self.setLayout(layout)

        if step:
            self.time.setValue(step["t"])
            for k,v in step["digital"].items():
                self.digs[k].setChecked(v)
            for k,v in step["analog"].items():
                self.anas[k].setValue(v)

    def get(self):
        return {
            "t": self.time.value(),
            "digital": {ch["key"]: self.digs[ch["key"]].isChecked() for ch in RELAY_CHANNELS},
            "analog": {k:self.anas[k].value() for k in ANALOG_CHANNELS}
        }

# -------------------------
# Editor Screen
# -------------------------

class Editor(QWidget):
    def __init__(self, data, mark_dirty):
        super().__init__()
        self.data = data
        self.mark_dirty = mark_dirty

        self.table = QTableWidget()
        self.table.setColumnCount(1 + len(RELAY_CHANNELS) + len(ANALOG_CHANNELS))
        self.table.setHorizontalHeaderLabels(
            ["Time"] + [ch["label"] for ch in RELAY_CHANNELS] + ANALOG_CHANNELS
        )

        add = QPushButton("Add")
        edit = QPushButton("Edit")
        delete = QPushButton("Delete")

        add.clicked.connect(self.add)
        edit.clicked.connect(self.edit)
        delete.clicked.connect(self.delete)

        btns = QHBoxLayout()
        btns.addWidget(add)
        btns.addWidget(edit)
        btns.addWidget(delete)

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addLayout(btns)
        self.setLayout(layout)

        self.refresh()

    def refresh(self):
        steps = self.data["steps"]
        self.table.setRowCount(len(steps))

        for r,s in enumerate(steps):
            self.table.setItem(r,0,QTableWidgetItem(str(s["t"])))
            c=1
            for ch in RELAY_CHANNELS:
                key = ch["key"]
                self.table.setItem(r, c, QTableWidgetItem(str(int(s["digital"][key]))))
                c+=1
            for a in ANALOG_CHANNELS:
                self.table.setItem(r,c,QTableWidgetItem(str(s["analog"][a])))
                c+=1

    def row(self):
        sel=self.table.selectionModel().selectedRows()
        return sel[0].row() if sel else -1

    def add(self):
        dlg=StepDialog(self)
        if dlg.exec():
            self.data["steps"].append(dlg.get())
            self.refresh()
            self.mark_dirty()

    def edit(self):
        r=self.row()
        if r<0: return
        dlg=StepDialog(self,self.data["steps"][r])
        if dlg.exec():
            self.data["steps"][r]=dlg.get()
            self.refresh()
            self.mark_dirty()

    def delete(self):
        r=self.row()
        if r<0: return
        del self.data["steps"][r]
        self.refresh()
        self.mark_dirty()

# -------------------------
# Main Window
# -------------------------

class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Preset Editor")

        self.stack=QStackedWidget()
        self.setCentralWidget(self.stack)

        self.file=None
        self.data=default_preset()
        self.dirty=False

        start=QWidget()
        new=QPushButton("Create New")
        open=QPushButton("Open")

        new.clicked.connect(self.new_file)
        open.clicked.connect(self.open_file)

        l=QVBoxLayout()
        l.addWidget(new)
        l.addWidget(open)
        start.setLayout(l)

        self.editor=Editor(self.data,self.mark_dirty)

        self.stack.addWidget(start)
        self.stack.addWidget(self.editor)

        save=QPushButton("Save")
        save.clicked.connect(self.save)
        self.statusBar().addPermanentWidget(save)

    def mark_dirty(self):
        self.dirty=True

    def new_file(self):
        path,_=QFileDialog.getSaveFileName(self,"Create",".","JSON (*.json)")
        if not path: return
        self.file=path
        self.data=default_preset()
        self.editor.data=self.data
        self.editor.refresh()
        self.stack.setCurrentIndex(1)

    def open_file(self):
        path,_=QFileDialog.getOpenFileName(self,"Open",".","JSON (*.json)")
        if not path: return
        self.file=path
        self.data=load_preset(path)
        self.editor.data=self.data
        self.editor.refresh()
        self.stack.setCurrentIndex(1)

    def save(self):
        if self.file:
            save_preset(self.file,self.data)
            self.dirty=False

def main():
    app=QApplication([])
    w=Main()
    w.show()
    app.exec()

if __name__=="__main__":
    main()
