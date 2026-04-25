"""
lora_comms.py
RFM95W LoRa communication module for Raspberry Pi 5.
Integrates with existing Python structures via LoRAComms class.

Hardware: Adafruit RFM95W on SPI0, CE0
Frequency: 915 MHz | SF7 | BW 125kHz | CR 4/5

pip install adafruit-circuitpython-rfm9x RPi.GPIO
Enable SPI: sudo raspi-config → Interface Options → SPI → Enable
"""

import time
import threading
import logging
import busio
import board
import digitalio
import adafruit_rfm9x

logger = logging.getLogger(__name__)


# ── Pin definitions ────────────────────────────────────────────────────────────
CS_PIN    = digitalio.DigitalInOut(board.CE0)   # GPIO 8
RESET_PIN = digitalio.DigitalInOut(board.D25)   # GPIO 25
IRQ_PIN   = board.D24                           # GPIO 24 (not directly used by lib)

# ── LoRa RF parameters ─────────────────────────────────────────────────────────
LORA_FREQ_MHZ       = 915.0
LORA_SF             = 7
LORA_BW             = 125000   # Hz — adafruit lib takes signal_bandwidth in Hz
LORA_CODING_RATE    = 5        # 4/5 → pass denominator only
LORA_TX_POWER       = 23       # dBm, 23 max for RFM95W
LORA_SYNC_WORD      = 0x12     # Private network (must match GRC side)
LORA_PREAMBLE_LEN   = 8

# ── Known command strings ──────────────────────────────────────────────────────
KNOWN_COMMANDS = {"Start", "Estop"}


class LoRAComms:
    """
    Two-way LoRa communication manager.

    Usage:
        comms = LoRAComms(command_callback=my_handler)
        comms.start()
        comms.send_telemetry("alt:120,spd:15.3,bat:92%")
        comms.stop()

    command_callback(cmd: str) is called from the RX thread whenever
    a recognised command is received.
    """

    def __init__(self, command_callback=None, poll_interval=0.05):
        """
        Args:
            command_callback: callable(cmd_string) triggered on valid command RX.
            poll_interval:    seconds between RX polls (default 50 ms).
        """
        self._callback = command_callback
        self._poll_interval = poll_interval
        self._running = False
        self._rx_thread = None
        self._tx_lock = threading.Lock()  # Prevent TX/RX collision

        # Initialise SPI bus and RFM95W
        spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        self.rfm9x = adafruit_rfm9x.RFM9x(
            spi, CS_PIN, RESET_PIN, LORA_FREQ_MHZ
        )

        # Apply RF parameters
        self.rfm9x.spreading_factor     = LORA_SF
        self.rfm9x.signal_bandwidth     = LORA_BW
        self.rfm9x.coding_rate          = LORA_CODING_RATE
        self.rfm9x.tx_power             = LORA_TX_POWER
        self.rfm9x.preamble_length      = LORA_PREAMBLE_LEN

        # Sync word — adafruit lib exposes this via the register directly
        # Register 0x39 is LoRa Sync Word
        self.rfm9x._write_u8(0x39, LORA_SYNC_WORD)

        # After initializing rfm9x, read back the register to confirm
        sync_val = self.rfm9x._read_u8(0x39)
        print(f"Sync word register 0x39 = 0x{sync_val:02X}  (expected 0x12)")



        self.last_message = " "

        logger.info(
            "RFM95W ready — %.1f MHz | SF%d | BW %d Hz | CR 4/%d | Sync 0x%02X",
            LORA_FREQ_MHZ, LORA_SF, LORA_BW, LORA_CODING_RATE, LORA_SYNC_WORD
        )

    # ── Public API ─────────────────────────────────────────────────────────────

    def start(self):
        """Start the background RX listener thread."""
        if self._running:
            return
        self._running = True
        self._rx_thread = threading.Thread(
            target=self._rx_loop, name="LoRa-RX", daemon=True
        )
        self._rx_thread.start()
        logger.info("LoRa RX listener started.")

    def stop(self):
        """Stop the background RX listener thread gracefully."""
        self._running = False
        if self._rx_thread:
            self._rx_thread.join(timeout=2.0)
        logger.info("LoRa comms stopped.")

    def send_telemetry(self, telemetry_string: str) -> bool:
        """
        Transmit a telemetry string to the ground station.

        Args:
            telemetry_string: plain text, e.g. "alt:120,spd:15.3,bat:92%"
                              Max ~252 bytes for LoRa payload.
        Returns:
            True if transmitted without error, False otherwise.
        """
        payload = telemetry_string.encode("utf-8")
        if len(payload) > 252:
            logger.warning("Telemetry string too long (%d bytes), truncating.", len(payload))
            payload = payload[:252]

        with self._tx_lock:
            try:
                self.rfm9x.send(payload)
                logger.debug("TX telemetry: %s", telemetry_string)
                return True
            except Exception as e:
                logger.error("TX failed: %s", e)
                return False

    @property
    def last_rssi(self) -> float:
        """RSSI of the last received packet in dBm."""
        return self.rfm9x.last_rssi



    # ── Internal RX loop ───────────────────────────────────────────────────────

    def _rx_loop(self):
        """Poll for incoming packets and dispatch commands."""
        while self._running:
            try:
                with self._tx_lock:
                    packet = self.rfm9x.receive(timeout=self._poll_interval)

                if packet is not None:
                    try:
                        message = packet.decode("utf-8").strip()
                        self.last_message = message
                    except UnicodeDecodeError:
                        logger.warning("RX: could not decode packet as UTF-8, ignoring.")
                        continue

                    rssi = self.rfm9x.last_rssi
                    logger.info("RX [RSSI %d dBm]: '%s'", rssi, message)

                    if message in KNOWN_COMMANDS:
                        logger.info("Valid command received: '%s'", message)
                        if self._callback:
                            try:
                                self._callback(message)
                            except Exception as e:
                                logger.error("Command callback raised exception: %s", e)
                    else:
                        logger.warning("Unknown command received: '%s'", message)

            except Exception as e:
                logger.error("RX loop error: %s", e)
                time.sleep(0.5)  # Back off briefly on hardware error