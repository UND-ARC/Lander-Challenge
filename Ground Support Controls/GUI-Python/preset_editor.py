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
AIN_CHANNELS = [f"AIN{i}" for i in range(56)]


# -------------------------
# Sensor definitions
# -------------------------

SENSOR_META = {
    # -------- CRYO RTDs (0–10V) --------
    "AIN0":  {"unit": "°C",  "v_min": 0.0, "v_max": 10.0, "e_min": -200.0, "e_max": 200.0},  # 0–10V → -200 to 200°C
    "AIN1":  {"unit": "°C",  "v_min": 0.0, "v_max": 10.0, "e_min": -200.0, "e_max": 200.0},

    # -------- CRYO PRESSURE (0–5V) --------
    "AIN8":  {"unit": "psi", "v_min": 0.0, "v_max": 5.0,  "e_min": 0.0, "e_max": 500.0},   # 0–5V → 0–500 psi

    # -------- EXAMPLE (0–10V → 0–1000 psi) --------
    "AIN19": {"unit": "psi", "v_min": 0.0, "v_max": 10.0, "e_min": 0.0, "e_max": 1000.0},  # 0–10V → 0–1000 psi
}

def eng_to_volts(ch, value):
    meta = SENSOR_META.get(ch)
    if not meta:
        return value

    v_min, v_max = meta["v_min"], meta["v_max"]
    e_min, e_max = meta["e_min"], meta["e_max"]

    return v_min + (value - e_min) * (v_max - v_min) / (e_max - e_min)


def volts_to_eng(ch, value):
    meta = SENSOR_META.get(ch)
    if not meta:
        return value

    v_min, v_max = meta["v_min"], meta["v_max"]
    e_min, e_max = meta["e_min"], meta["e_max"]

    return e_min + (value - v_min) * (e_max - e_min) / (v_max - v_min)

# -------------------------
# Data helpers
# -------------------------

def default_preset():
    return {
        "version": 2,
        "thresholds": {},
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
            "analog": {
                k: (self.anas[k].value() * 5.0 / 100.0)
                for k in ANALOG_CHANNELS
            }
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
        self.threshold_table = QTableWidget()
        self.threshold_table.setColumnCount(3)
        self.threshold_table.setHorizontalHeaderLabels(["Channel", "Threshold", "Units/Range"])
        self.table.setColumnCount(1 + len(RELAY_CHANNELS) + len(ANALOG_CHANNELS))
        self.table.setHorizontalHeaderLabels(
            ["Time"] + [ch["label"] for ch in RELAY_CHANNELS] + ANALOG_CHANNELS
        )

        add = QPushButton("Add Event Row")
        edit = QPushButton("Edit Event Row")
        delete = QPushButton("Delete Event Row")

        add.clicked.connect(self.add)
        edit.clicked.connect(self.edit)
        delete.clicked.connect(self.delete)

        btns = QHBoxLayout()
        btns.addWidget(add)
        btns.addWidget(edit)
        btns.addWidget(delete)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Sensor Thresholds"))
        layout.addWidget(self.threshold_table)

        layout.addWidget(self.table)
        layout.addLayout(btns)
        self.setLayout(layout)

        self.refresh()

    def refresh(self):
        thresholds = self.data.get("thresholds", {})
        self.threshold_table.setRowCount(len(AIN_CHANNELS))

        for r, ch in enumerate(AIN_CHANNELS):
            self.threshold_table.setItem(r, 0, QTableWidgetItem(ch))

            val = thresholds.get(ch, "")
            if val != "":
                eng_val = volts_to_eng(ch, val)
                self.threshold_table.setItem(r, 1, QTableWidgetItem(f"{eng_val:.2f}"))
            else:
                self.threshold_table.setItem(r, 1, QTableWidgetItem(""))

            meta = SENSOR_META.get(ch)

            if meta:
                unit = meta["unit"]
                e_min = meta["e_min"]
                e_max = meta["e_max"]
                v_min = meta["v_min"]
                v_max = meta["v_max"]

                text = f"{unit} ({e_min:g} - {e_max:g}) | {v_min:g} - {v_max:g}V"
            else:
                text = "volts (raw)"

            item = QTableWidgetItem(text)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.threshold_table.setItem(r, 2, item)

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
                volts = s["analog"][a]
                percent = volts * 100.0 / 5.0
                self.table.setItem(r, c, QTableWidgetItem(f"{percent:.1f}"))
                c+=1

    def collect_thresholds(self):
        thresholds = {}

        for r in range(self.threshold_table.rowCount()):
            ch_item = self.threshold_table.item(r, 0)
            val_item = self.threshold_table.item(r, 1)

            if ch_item and val_item:
                ch = ch_item.text()
                raw = val_item.text()

                try:
                    eng_val = float(raw)
                    volt_val = eng_to_volts(ch, eng_val)
                    thresholds[ch] = volt_val
                except:
                    pass

        self.data["thresholds"] = thresholds

    def collect_steps(self):
        steps = []

        for r in range(self.table.rowCount()):
            try:
                step = {
                    "t": float(self.table.item(r, 0).text()),
                    "digital": {},
                    "analog": {}
                }

                c = 1
                for ch in RELAY_CHANNELS:
                    item = self.table.item(r, c)
                    step["digital"][ch["key"]] = bool(int(item.text())) if item else False
                    c += 1

                for a in ANALOG_CHANNELS:
                    item = self.table.item(r, c)
                    percent = float(item.text()) if item else 0.0
                    volts = percent * 5.0 / 100.0
                    step["analog"][a] = volts
                    c += 1

                steps.append(step)
            except:
                pass

        self.data["steps"] = steps

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
            self.editor.collect_thresholds()
            self.editor.collect_steps()
            save_preset(self.file, self.data)
            self.dirty = False

def main():
    app=QApplication([])
    w=Main()
    w.show()
    app.exec()

if __name__=="__main__":
    main()
