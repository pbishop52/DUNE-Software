import time
import sys
from time import sleep

from robust_serial import Order, read_order, write_i8, write_order
from robust_serial.utils import open_serial_port
from gui_test import MainWindow  # Assuming your PyQt5 GUI is in a file named gui.py
from PyQt5.QtWidgets import QApplication

def initialize_arduino():
    """
    Initialize communication with the Arduino.
    Returns a connected serial file object.
    """
    try:
        serial_file = open_serial_port(baudrate=115200, timeout=None)
    except Exception as e:
        print(f"Error opening serial port: {e}")
        sys.exit(1)

    is_connected = False
    # Wait for Arduino to respond
    start_time = time.time()
    while not is_connected:
        print("Waiting for Arduino...")
        write_order(serial_file, Order.HELLO)

        if serial_file.in_waiting > 0:
            byte = serial_file.read(1)[0]  # Read single byte
            if byte in [Order.HELLO.value, Order.ALREADY_CONNECTED.value]:
                is_connected = True
                write_order(serial_file, Order.ALREADY_CONNECTED)
                print("Connected to Arduino")
                return serial_file

        if time.time() - start_time > 10:  # 10-second timeout
            print("Error: Arduino not responding.")
            sys.exit(1)

        time.sleep(2)  # Retry every 2 seconds

    return serial_file

def main():
    """
    Main function to start GUI and testing process.
    """
    serial_file = initialize_arduino()

    app = QApplication(sys.argv)
    window = MainWindow(serial_file)  # Pass serial connection to GUI
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
