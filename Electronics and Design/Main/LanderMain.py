import time
import sys
import logging
import threading

from lora_comms import LoRAComms
from RadioModule import LanderRadio
from GPSModule import LanderGPS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)

# ── Your application state ─────────────────────────────────────────────────────
system_running = False
estop_active   = False
state_lock     = threading.Lock()

def handle_command(cmd: str):
    """
    Called by LoRAComms RX thread when a valid command arrives.
    Runs in the RX thread — use locks if modifying shared state.
    """
    global system_running, estop_active

    with state_lock:
        if cmd == "Start":
            if estop_active:
                print("[CMD] Start received but ESTOP is active — ignoring.")
            else:
                system_running = True
                print("[CMD] START command received — system running.")

        elif cmd == "Estop":
            system_running = False
            estop_active   = True
            print("[CMD] *** ESTOP RECEIVED — ALL OPERATIONS HALTED ***")


def collect_telemetry() -> str:
    """
    Build your telemetry string here.
    Replace with real sensor reads from your existing code.
    """
    # Example — swap in your actual data sources
    altitude  = 120.5
    speed     = 15.3
    battery   = 92
    estop     = estop_active
    running   = system_running

    return f"alt:{altitude:.1f},spd:{speed:.1f},bat:{battery}%,run:{int(running)},estop:{int(estop)}"

def main():
    print("Starting lander main program....")

    #start up the radio and wait for start command
    radio = LoRAComms(command_callback=handle_command)
    radio.start()

    print("Waiting for start command...")
    #wait for radio to receive start command
    while not system_running:
        time.sleep(1)
        print(f"last rssi:    {radio.last_rssi}")
        print(f"last message: {radio.last_message}")

    #start up the other sensors ....


    while system_running:
        telemetry = collect_telemetry()
        success = radio.send_telemetry(telemetry)
        if success:
            print(f"[TX] {telemetry}")
        time.sleep(2.0)




if __name__ == "__main__":
    main()




