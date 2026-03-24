import csv
import json
import queue
import struct
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import deque

import numpy as np
from dearpygui import dearpygui as dpg
from labjack import ljm


# ============================================================
# SETTINGS
# ============================================================
GUI_HZ = 10.0
WINDOW_SECONDS = 10.0

MIN_STREAM_HZ = 5
MAX_STREAM_HZ = 500
DEFAULT_STREAM_HZ = 100.0

DEFAULT_THRESHOLD_V = 12.0
DEFAULT_SHUTDOWN_PIN = "FIO7"

# T7 reads these inputs
AIN_NAMES = ["AIN0", "AIN1", "AIN2"]

# T4 controls these outputs
DIGITAL_OUTPUTS = [
    ("FIO4", "D0 (FIO4)"),
    ("FIO5", "D1 (FIO5)"),
    ("FIO6", "D2 (FIO6)"),
    ("FIO7", "D3 (FIO7)"),
]

CONFIG_D_MAP = {
    "D0": "FIO4",
    "D1": "FIO5",
    "D2": "FIO6",
    "D3": "FIO7",
}

CONFIG_A_MAP = {
    "A0": "DAC0",
    "A1": "DAC1",
}

Y_MIN = -0.1
Y_MAX = 5.1


# ============================================================
# HELPERS
# ============================================================
def stamp_now() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


@dataclass
class EventItem:
    t: float
    msg: str


@dataclass
class RawBlock:
    start_index: int
    n_scans: int
    data: np.ndarray  # shape (n_scans, n_channels), float32


@dataclass
class ConfigStep:
    t: float = 0.0
    digital: Dict[str, bool] = field(default_factory=dict)
    analog: Dict[str, float] = field(default_factory=dict)


class ChannelDisplayRing:
    def __init__(self, channel_names: List[str], seconds: float, hz: float):
        self.channel_names = list(channel_names)
        self.reset(seconds, hz)

    def reset(self, seconds: float, hz: float):
        self.seconds = float(seconds)
        self.hz = float(hz)
        self.capacity = max(32, int(np.ceil(self.seconds * self.hz)) + 32)

        self.t = np.empty(self.capacity, dtype=np.float64)
        self.y = {
            ch: np.empty(self.capacity, dtype=np.float32)
            for ch in self.channel_names
        }

        self.write_idx = 0
        self.size = 0
        self.lock = threading.Lock()

    def append_block(self, t_new: np.ndarray, y_new: np.ndarray):
        if t_new.size == 0:
            return

        t_new = np.asarray(t_new, dtype=np.float64)
        y_new = np.asarray(y_new, dtype=np.float32)

        n = len(t_new)
        if y_new.shape != (n, len(self.channel_names)):
            return

        if n >= self.capacity:
            t_new = t_new[-self.capacity:]
            y_new = y_new[-self.capacity:, :]
            n = self.capacity

        with self.lock:
            end = self.write_idx + n

            if end <= self.capacity:
                self.t[self.write_idx:end] = t_new
                for i, ch in enumerate(self.channel_names):
                    self.y[ch][self.write_idx:end] = y_new[:, i]
            else:
                first = self.capacity - self.write_idx
                second = n - first

                self.t[self.write_idx:] = t_new[:first]
                self.t[:second] = t_new[first:]

                for i, ch in enumerate(self.channel_names):
                    self.y[ch][self.write_idx:] = y_new[:first, i]
                    self.y[ch][:second] = y_new[first:, i]

            self.write_idx = (self.write_idx + n) % self.capacity
            self.size = min(self.size + n, self.capacity)

    def snapshot_channel(self, ch: str) -> Tuple[np.ndarray, np.ndarray]:
        with self.lock:
            if self.size == 0:
                return (
                    np.empty((0,), dtype=np.float64),
                    np.empty((0,), dtype=np.float32),
                )

            start = (self.write_idx - self.size) % self.capacity

            if start < self.write_idx:
                return (
                    self.t[start:self.write_idx].copy(),
                    self.y[ch][start:self.write_idx].copy(),
                )

            t = np.concatenate((self.t[start:], self.t[:self.write_idx]))
            y = np.concatenate((self.y[ch][start:], self.y[ch][:self.write_idx]))
            return t, y

    def snapshot(self) -> Tuple[np.ndarray, np.ndarray]:
        with self.lock:
            if self.size == 0:
                return (
                    np.empty((0,), dtype=np.float64),
                    np.empty((0, self.n_channels), dtype=np.float32),
                )

            start = (self.write_idx - self.size) % self.capacity

            if start < self.write_idx:
                return (
                    self.t[start:self.write_idx].copy(),
                    self.y[start:self.write_idx].copy(),
                )

            t = np.concatenate((self.t[start:], self.t[:self.write_idx]))
            y = np.concatenate((self.y[start:], self.y[:self.write_idx]), axis=0)
            return t, y


# ============================================================
# APP
# ============================================================
class LabJackApp:
    def __init__(self):
        self.t7_handle: Optional[int] = None
        self.t4_handle: Optional[int] = None

        self.stop_event = threading.Event()
        self.run_lock = threading.Lock()

        self.requested_stream_hz = DEFAULT_STREAM_HZ
        self.actual_stream_hz = 0.0
        self.threshold_v = DEFAULT_THRESHOLD_V
        self.shutdown_pin = DEFAULT_SHUTDOWN_PIN

        self.app_start = time.perf_counter()

        self.raw_queue: queue.Queue[RawBlock] = queue.Queue()
        self.display_queue: queue.Queue[RawBlock] = queue.Queue(maxsize=200)
        self.event_queue: queue.Queue[EventItem] = queue.Queue()

        self.display_ring = ChannelDisplayRing(AIN_NAMES, WINDOW_SECONDS, GUI_HZ)
        self.latest_display_values = {ch: float("nan") for ch in AIN_NAMES}

        self.stream_thread: Optional[threading.Thread] = None
        self.logger_thread: Optional[threading.Thread] = None

        self.latest_device_backlog = 0
        self.latest_ljm_backlog = 0

        self.bin_path = ""
        self.events_path = ""
        self.csv_path = ""

        self.loaded_config_name = "None"
        self.loaded_config_path = ""
        self.loaded_steps: List[ConfigStep] = []

        self.scheduled_timers: List[threading.Timer] = []
        self.scheduled_timers_lock = threading.Lock()

        self.dio_states = {name: 0 for name, _ in DIGITAL_OUTPUTS}

        self._last_gui_update = 0.0
        self._status_text = "Status: starting…"
        self._gui_state_lock = threading.Lock()
        self._updating_dio_widgets = False

        self._build_gui()
        self.start_run()

    # ----------------------------
    # Logging helpers
    # ----------------------------
    def log_event(self, msg: str):
        t = time.perf_counter() - self.app_start
        try:
            self.event_queue.put_nowait(EventItem(t=t, msg=msg))
        except queue.Full:
            pass

    def _set_status(self, text: str):
        with self._gui_state_lock:
            self._status_text = text

    def open_labjack(self):
        self.t7_handle = None
        self.t4_handle = None

        try:
            self.t7_handle = ljm.openS("T7", "ANY", "ANY")
            self.log_event("T7 CONNECTED")
        except Exception as e:
            self.log_event(f"T7 NOT FOUND: {e}")

        try:
            self.t4_handle = ljm.openS("T4", "ANY", "ANY")
            self.log_event("T4 CONNECTED")
        except Exception as e:
            self.log_event(f"T4 NOT FOUND: {e}")

        self._set_status(
            f"T7={'OK' if self.t7_handle is not None else 'MISSING'} | "
            f"T4={'OK' if self.t4_handle is not None else 'MISSING'}"
        )

    def close_labjack(self):
        if self.t7_handle is not None:
            try:
                ljm.eStreamStop(self.t7_handle)
            except Exception:
                pass

        for handle in (self.t7_handle, self.t4_handle):
            if handle is not None:
                try:
                    ljm.close(handle)
                except Exception:
                    pass

        self.t7_handle = None
        self.t4_handle = None

        time.sleep(0.2)

    def set_dio(self, dio_name: str, value: int, do_log: bool = True):
        if self.t4_handle is None:
            return
        try:
            ljm.eWriteName(self.t4_handle, dio_name, int(value))
            self.dio_states[dio_name] = int(value)
            if do_log:
                self.log_event(f"BUTTON {dio_name}={int(value)}")
        except Exception as e:
            self._set_status(f"DIO error on {dio_name}: {e}")

    def set_dac(self, dac_name: str, value: float, do_log: bool = True):
        if self.t4_handle is None:
            return
        try:
            ljm.eWriteName(self.t4_handle, dac_name, float(value))
            if do_log:
                self.log_event(f"ANALOG_OUT {dac_name}={float(value):.6f}")
        except Exception as e:
            self._set_status(f"DAC error on {dac_name}: {e}")

    # ----------------------------
    # Run lifecycle
    # ----------------------------
    def start_run(self):
        with self.run_lock:
            self.stop_event.clear()
            self.display_ring.reset(WINDOW_SECONDS, GUI_HZ)
            self.latest_display_values = {ch: float("nan") for ch in AIN_NAMES}
            self._clear_queues()

            self.app_start = time.perf_counter()
            self.actual_stream_hz = 0.0
            self.latest_device_backlog = 0
            self.latest_ljm_backlog = 0

            stamp = stamp_now()
            self.bin_path = f"rawlog_{stamp}.bin"
            self.events_path = f"events_{stamp}.csv"
            self.csv_path = f"data_{stamp}.csv"

            self.open_labjack()

            try:
                ljm.eWriteName(self.t4_handle, self.shutdown_pin, 0.0)
            except Exception:
                pass

            # Set all T4 digital outputs low
            for dio_name, _label in DIGITAL_OUTPUTS:
                self.set_dio(dio_name, 0, do_log=False)

            self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
            self.stream_thread.start()

            t0 = time.perf_counter()
            while self.actual_stream_hz <= 0.0 and not self.stop_event.is_set():
                if time.perf_counter() - t0 > 2.0:
                    self._set_status("Stream did not start.")
                    break
                time.sleep(0.01)

            self.logger_thread = threading.Thread(target=self._logger_loop, daemon=True)
            self.logger_thread.start()

            self.log_event(
                f"APP_START requested={self.requested_stream_hz} actual={self.actual_stream_hz}"
            )
            self._set_status(
                f"Streaming actual={self.actual_stream_hz:.1f} Hz (req {self.requested_stream_hz:.0f})"
            )

    def stop_run(self):
        with self.run_lock:
            self.cancel_all_scheduled_steps()
            self.stop_event.set()

            for th in (self.stream_thread, self.logger_thread):
                if th and th.is_alive():
                    th.join(timeout=3.0)

            self.stream_thread = None
            self.logger_thread = None

            self.close_labjack()

    def restart_run(self):
        self.stop_run()
        time.sleep(0.3)
        self.start_run()

    def kill_switch(self):
        self.stop_run()
        self.build_csv_if_possible()
        dpg.stop_dearpygui()

    def _clear_queues(self):
        while not self.raw_queue.empty():
            try:
                self.raw_queue.get_nowait()
            except queue.Empty:
                break

        while not self.display_queue.empty():
            try:
                self.display_queue.get_nowait()
            except queue.Empty:
                break

        while not self.event_queue.empty():
            try:
                self.event_queue.get_nowait()
            except queue.Empty:
                break

    # ----------------------------
    # Stream thread (T7 inputs)
    # ----------------------------
    def _stream_loop(self):
        if self.t7_handle is None:
            self._set_status("No T7 connected → no data")
            return
        try:
            addrs, _ = ljm.namesToAddresses(len(AIN_NAMES), AIN_NAMES)
            n_ch = len(addrs)

            scans_per_read = int(self.requested_stream_hz / 2)
            scans_per_read = max(1, min(scans_per_read, 1000))

            try:
                ljm.eWriteName(self.t7_handle, "STREAM_CLOCK_SOURCE", 0)
                ljm.eWriteName(self.t7_handle, "STREAM_SETTLING_US", 0)
                ljm.eWriteName(self.t7_handle, "STREAM_RESOLUTION_INDEX", 1)

                for ain in AIN_NAMES:
                    ljm.eWriteName(self.t7_handle, f"{ain}_RANGE", 10.0)
                    ljm.eWriteName(self.t7_handle, f"{ain}_NEGATIVE_CH", 199)
                    ljm.eWriteName(self.t7_handle, f"{ain}_RESOLUTION_INDEX", 1)
                    ljm.eWriteName(self.t7_handle, f"{ain}_SETTLING_US", 0)

            except Exception as e:
                self._set_status(f"Stream config warning: {e}")

            actual = ljm.eStreamStart(
                self.t7_handle,
                scans_per_read,
                n_ch,
                addrs,
                self.requested_stream_hz,
            )
            self.actual_stream_hz = float(actual)
            self._set_status(f"T7 streaming @ {self.actual_stream_hz:.1f} Hz")
            sample_index = 0

            self.log_event(f"STREAM_START actual={self.actual_stream_hz:.3f} SPR={scans_per_read}")

            while not self.stop_event.is_set():
                data, device_backlog, ljm_backlog = ljm.eStreamRead(self.t7_handle)
                self.latest_device_backlog = int(device_backlog)
                self.latest_ljm_backlog = int(ljm_backlog)

                arr = np.asarray(data, dtype=np.float32)
                if arr.size == 0:
                    continue

                n_scans = arr.size // n_ch
                if n_scans <= 0:
                    continue

                arr = arr[: n_scans * n_ch].reshape((n_scans, n_ch))

                threshold_v = float(self.threshold_v)

                valid = np.isfinite(arr)

                if threshold_v > 0.0 and np.any(valid & (arr > threshold_v)):
                    max_seen = float(np.nanmax(arr[valid])) if np.any(valid) else float("nan")
                    self.log_event(
                        f"THRESHOLD_TRIGGERED threshold={threshold_v:.6f}V max_seen={max_seen:.6f}V"
                    )
                    try:
                        if self.t4_handle is not None:
                            ljm.eWriteName(self.t4_handle, self.shutdown_pin, 1.0)
                    except Exception:
                        pass
                    self.stop_event.set()
                    self._set_status(
                        f"Threshold triggered: max={max_seen:.3f} V > threshold={threshold_v:.3f} V"
                    )
                    break

                block = RawBlock(
                    start_index=sample_index,
                    n_scans=n_scans,
                    data=arr,
                )

                self.raw_queue.put(block)

                try:
                    self.display_queue.put_nowait(block)
                except queue.Full:
                    pass

                sample_index += n_scans

        except Exception as e:
            self.log_event(f"STREAM_ERROR {e}")
            self._set_status(f"Stream error: {e}")
            self.stop_event.set()
        finally:
            if self.t7_handle is not None:
                try:
                    ljm.eStreamStop(self.t7_handle)
                except Exception:
                    pass
            self.log_event("STREAM_STOP")

    # ----------------------------
    # Logger thread
    # ----------------------------
    def _logger_loop(self):
        try:
            with open(self.bin_path, "wb") as bin_f, open(
                self.events_path, "w", newline="", encoding="utf-8"
            ) as evt_f:
                bin_f.write(b"LJBLK1\0\0")
                bin_f.write(struct.pack("<I", 1))
                bin_f.write(struct.pack("<I", len(AIN_NAMES)))
                bin_f.write(struct.pack("<d", float(self.actual_stream_hz)))

                evt_writer = csv.writer(evt_f)
                evt_writer.writerow(["time", "event"])

                last_flush = time.perf_counter()

                while not self.stop_event.is_set():
                    while True:
                        try:
                            ev = self.event_queue.get_nowait()
                        except queue.Empty:
                            break
                        evt_writer.writerow([f"{ev.t:.6f}", ev.msg])

                    try:
                        block = self.raw_queue.get(timeout=0.2)
                    except queue.Empty:
                        block = None

                    if block is not None:
                        bin_f.write(struct.pack("<Q", int(block.start_index)))
                        bin_f.write(struct.pack("<I", int(block.n_scans)))
                        bin_f.write(block.data.tobytes(order="C"))

                    now = time.perf_counter()
                    if now - last_flush >= 1.0:
                        bin_f.flush()
                        evt_f.flush()
                        last_flush = now

                while True:
                    try:
                        ev = self.event_queue.get_nowait()
                    except queue.Empty:
                        break
                    evt_writer.writerow([f"{ev.t:.6f}", ev.msg])

                while not self.display_queue.empty():
                    try:
                        block = self.display_queue.get_nowait()
                    except queue.Empty:
                        break
                    bin_f.write(struct.pack("<Q", int(block.start_index)))
                    bin_f.write(struct.pack("<I", int(block.n_scans)))
                    bin_f.write(block.data.tobytes(order="C"))

                bin_f.flush()
                evt_f.flush()

        except Exception as e:
            self._set_status(f"Logger error: {e}")

    # ----------------------------
    # CSV export
    # ----------------------------
    def build_csv_if_possible(self):
        if not self.bin_path or not Path(self.bin_path).exists():
            return

        try:
            with open(self.bin_path, "rb") as in_f, open(
                self.csv_path, "w", newline="", encoding="utf-8"
            ) as out_f:
                magic = in_f.read(8)
                if magic != b"LJBLK1\0\0":
                    self._set_status("CSV export error: invalid binary header")
                    return

                version = struct.unpack("<I", in_f.read(4))[0]
                n_channels = struct.unpack("<I", in_f.read(4))[0]
                actual_scan_hz = struct.unpack("<d", in_f.read(8))[0]

                if version != 1 or n_channels != len(AIN_NAMES) or actual_scan_hz <= 0.0:
                    self._set_status("CSV export error: invalid binary metadata")
                    return

                writer = csv.writer(out_f)
                writer.writerow(["time"] + AIN_NAMES)

                block_header_size = struct.calcsize("<QI")

                while True:
                    hdr = in_f.read(block_header_size)
                    if not hdr or len(hdr) < block_header_size:
                        break

                    start_index, n_scans = struct.unpack("<QI", hdr)
                    raw = in_f.read(n_scans * n_channels * 4)
                    if len(raw) < n_scans * n_channels * 4:
                        break

                    data = np.frombuffer(raw, dtype=np.float32).reshape((n_scans, n_channels))

                    rows = []
                    for i in range(n_scans):
                        t = (start_index + i) / actual_scan_hz
                        rows.append([f"{t:.6f}"] + [f"{float(v):.6f}" for v in data[i]])
                    writer.writerows(rows)

            self._set_status(f"Saved CSV: {self.csv_path}")
        except Exception as e:
            self._set_status(f"CSV export error: {e}")

    # ----------------------------
    # Config / preset
    # ----------------------------
    def _load_config_from_path(self, path: str):
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
        except Exception as e:
            self._set_status(f"Config load error: {e}")
            return

        try:
            name = ""
            steps_raw = []

            if isinstance(obj, dict) and "steps" in obj and isinstance(obj["steps"], list):
                name = str(obj.get("name", "") or "")
                steps_raw = obj["steps"]
            elif (
                isinstance(obj, dict)
                and "preset" in obj
                and isinstance(obj["preset"], dict)
            ):
                p = obj["preset"]
                name = str(p.get("name", "") or "")
                steps_raw = p.get("steps", [])
            else:
                self._set_status("Invalid config format.")
                return

            loaded_steps: List[ConfigStep] = []
            for s in steps_raw:
                if not isinstance(s, dict):
                    continue

                digital = s.get("digital", {}) or {}
                analog = s.get("analog", {}) or {}
                if not isinstance(digital, dict):
                    digital = {}
                if not isinstance(analog, dict):
                    analog = {}

                step = ConfigStep(
                    t=float(s.get("t", 0.0)),
                    digital=dict(digital),
                    analog=dict(analog),
                )
                loaded_steps.append(step)

            self.loaded_config_name = name or Path(path).stem
            self.loaded_config_path = path
            self.loaded_steps = loaded_steps

            dpg.set_value(
                "cfg_loaded_text",
                f"Loaded: {self.loaded_config_name} ({Path(path).name})",
            )
            self.log_event(f'CONFIG_LOADED "{self.loaded_config_name}" steps={len(self.loaded_steps)}')
            self._set_status(f"Loaded preset: {Path(path).name}")

        except Exception as e:
            self._set_status(f"Config parse error: {e}")

    def _on_file_selected(self, sender, app_data):
        try:
            selections = app_data.get("selections", {})
            if selections:
                path = list(selections.values())[0]
                self._load_config_from_path(path)
        except Exception as e:
            self._set_status(f"File select error: {e}")

    def activate_loaded_config(self):
        if not self.loaded_steps:
            self._set_status("No configuration loaded.")
            return

        self.cancel_all_scheduled_steps()
        self.log_event(f'CONFIG_START "{self.loaded_config_name}" steps={len(self.loaded_steps)}')

        with self.scheduled_timers_lock:
            for step in self.loaded_steps:
                delay = max(0.0, float(step.t))
                timer = threading.Timer(delay, self._run_config_step, args=(step,))
                timer.daemon = True
                timer.start()
                self.scheduled_timers.append(timer)

        self._set_status(f'Preset running: {self.loaded_config_name}')

    def _run_config_step(self, step: ConfigStep):
        parts = []

        for dkey, fio in CONFIG_D_MAP.items():
            if dkey in step.digital:
                value = 1 if bool(step.digital[dkey]) else 0
                self.set_dio(fio, value, do_log=False)
                parts.append(f"{dkey}={value}")

        for akey, dac in CONFIG_A_MAP.items():
            if akey in step.analog:
                try:
                    value = float(step.analog[akey])
                except Exception:
                    value = 0.0
                self.set_dac(dac, value, do_log=False)
                parts.append(f"{akey}={value:.6f}")

        if parts:
            self.log_event("CONFIG_STEP " + " ".join(parts))
        else:
            self.log_event("CONFIG_STEP (no outputs)")

    def cancel_all_scheduled_steps(self):
        with self.scheduled_timers_lock:
            for timer in self.scheduled_timers:
                try:
                    timer.cancel()
                except Exception:
                    pass
            if self.scheduled_timers:
                self.log_event("CONFIG_STOP")
            self.scheduled_timers.clear()

    # ----------------------------
    # GUI
    # ----------------------------
    def _build_gui(self):
        dpg.create_context()

        with dpg.file_dialog(
            directory_selector=False,
            show=False,
            callback=self._on_file_selected,
            tag="file_dialog",
            width=900,
            height=600,
        ):
            dpg.add_file_extension(".json", color=(0, 255, 0, 255))
            dpg.add_file_extension(".*")

        with dpg.window(label="LabJack T7/T4 DAQ", tag="main_window"):
            dpg.add_text("Status: starting…", tag="status_text")

            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_text("Stream Hz:")
                dpg.add_input_int(
                    default_value=int(self.requested_stream_hz),
                    min_value=MIN_STREAM_HZ,
                    max_value=MAX_STREAM_HZ,
                    width=120,
                    tag="stream_hz_input",
                )
                dpg.add_button(label="Apply Stream Rate", callback=lambda: self._on_restart())

                dpg.add_text("Threshold (V):")
                dpg.add_input_float(
                    default_value=float(self.threshold_v),
                    width=120,
                    format="%.3f",
                    tag="threshold_input",
                    callback=lambda: self._on_threshold_change(),
                )

                dpg.add_button(label="Stop + Save CSV + Exit", callback=lambda: self.kill_switch())

            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_button(label="Load Preset (.json)", callback=lambda: dpg.show_item("file_dialog"))
                dpg.add_button(label="Start Preset", callback=lambda: self.activate_loaded_config())
                dpg.add_button(label="Stop Preset", callback=lambda: self.cancel_all_scheduled_steps())

            dpg.add_text("Loaded: None", tag="cfg_loaded_text")

            dpg.add_separator()

            with dpg.group(horizontal=True):
                with dpg.child_window(width=320, height=-1, border=True):
                    dpg.add_text("Outputs on T4")
                    dpg.add_separator()

                    for dio_name, label in DIGITAL_OUTPUTS:
                        dpg.add_checkbox(
                            label=label,
                            default_value=False,
                            tag=f"dio_checkbox_{dio_name}",
                            callback=lambda s, a, u=dio_name: self._on_dio_toggle(u),
                        )

                    dpg.add_separator()
                    dpg.add_text("", tag="metrics_text")

                with dpg.child_window(width=-1, height=-1, border=False):
                    dpg.add_text("Inputs streamed from T7")
                    for ch in AIN_NAMES:
                        with dpg.plot(
                                label=f"{ch} (last {int(WINDOW_SECONDS)}s)",
                                height=290,
                                width=-1,
                                no_menus=True,
                                no_box_select=True,
                                no_mouse_pos=True
                        ):
                            dpg.add_plot_legend()
                            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag=f"x_axis_{ch}")
                            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Voltage", tag=f"y_axis_{ch}")
                            dpg.set_axis_limits(y_axis, Y_MIN, Y_MAX)
                            dpg.add_line_series([], [], parent=y_axis, tag=f"series_{ch}", label=ch)

        dpg.create_viewport(
            title="LabJack T7/T4 DAQ",
            width=1800,
            height=1100,
            resizable=True,
        )
        dpg.setup_dearpygui()
        dpg.show_viewport()

        dpg.set_primary_window("main_window", True)

        def _resize_callback():
            if dpg.does_item_exist("main_window"):
                dpg.configure_item(
                    "main_window",
                    width=dpg.get_viewport_client_width(),
                    height=dpg.get_viewport_client_height(),
                )

        _resize_callback()
        dpg.set_viewport_resize_callback(lambda sender, app_data: _resize_callback())

    def _on_restart(self):
        val = dpg.get_value("stream_hz_input")
        val = max(MIN_STREAM_HZ, min(MAX_STREAM_HZ, int(val)))
        self.requested_stream_hz = float(val)
        self.restart_run()

    def _on_threshold_change(self):
        val = float(dpg.get_value("threshold_input"))
        if val < 0.0:
            val = 0.0
        self.threshold_v = val
        self.log_event(f"THRESHOLD_SET {val:.6f}")

    def _on_dio_toggle(self, dio_name: str):
        if self._updating_dio_widgets:
            return
        checked = bool(dpg.get_value(f"dio_checkbox_{dio_name}"))
        self.set_dio(dio_name, 1 if checked else 0, do_log=True)

    # ----------------------------
    # GUI update
    # ----------------------------
    def _drain_display_queue(self):
        scan_hz = self.actual_stream_hz
        if scan_hz <= 0.0:
            return

        decim = max(1, int(scan_hz / GUI_HZ))

        while True:
            try:
                block = self.display_queue.get_nowait()
            except queue.Empty:
                break

            idxs = slice(0, block.n_scans, decim)
            if idxs.size == 0:
                continue

            t_out = (block.start_index + np.arange(0, block.n_scans, decim)) / scan_hz
            y_out = block.data[idxs]

            self.display_ring.append_block(t_out, y_out)

            last_row = y_out[-1]
            for i, ch in enumerate(AIN_NAMES):
                self.latest_display_values[ch] = float(last_row[i])

    def update_gui(self):
        now = time.perf_counter()
        if now - self._last_gui_update < (1.0 / GUI_HZ):
            return
        self._last_gui_update = now

        self._drain_display_queue()

        for ch in AIN_NAMES:
            MAX_POINTS = 300

            t, y = self.display_ring.snapshot_channel(ch)
            if t.size >= 2:
                if t.size > MAX_POINTS:
                    idx = np.linspace(0, t.size - 1, MAX_POINTS).astype(np.int64)
                    t = t[idx]
                    y = y[idx]

                t_disp = t - float(t[-1])
                dpg.set_value(f"series_{ch}", [t_disp, y])
                dpg.set_axis_limits(f"x_axis_{ch}", -WINDOW_SECONDS, 0.0)

        with self._gui_state_lock:
            dpg.set_value("status_text", self._status_text)

        self._updating_dio_widgets = True
        try:
            for dio_name, _label in DIGITAL_OUTPUTS:
                tag = f"dio_checkbox_{dio_name}"
                current = dpg.get_value(tag)
                target = bool(self.dio_states[dio_name])
                if current != target:
                    dpg.set_value(tag, target)
        finally:
            self._updating_dio_widgets = False

        dpg.set_value(
            "metrics_text",
            f"inputs device=T7\n"
            f"outputs device=T4\n"
            f"actual={self.actual_stream_hz:.1f} Hz (req {self.requested_stream_hz:.0f})\n"
            f"device backlog={self.latest_device_backlog}\n"
            f"ljm backlog={self.latest_ljm_backlog}\n"
            f"threshold={self.threshold_v:.3f} V\n"
            f"AIN0 display={self.latest_display_values['AIN0']:.6f}\n"
            f"AIN1 display={self.latest_display_values['AIN1']:.6f}\n"
            f"AIN2 display={self.latest_display_values['AIN2']:.6f}\n"
            f"binary={self.bin_path}\n"
            f"events={self.events_path}\n"
            f"csv={self.csv_path}\n"
            f"preset={self.loaded_config_name}"
        )

    def run(self):
        try:
            while dpg.is_dearpygui_running():
                self.update_gui()
                dpg.render_dearpygui_frame()
        finally:
            self.stop_run()
            self.build_csv_if_possible()
            dpg.destroy_context()


if __name__ == "__main__":
    app = LabJackApp()
    app.run()