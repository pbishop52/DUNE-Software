import time
import csv
import numpy as np
import pyvisa
from time import sleep
from robust_serial import Order, read_order, write_i8, write_i16, write_order
from robust_serial.utils import open_serial_port, setRelay  # Import setRelay function
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QGridLayout, QComboBox, QFileDialog, QTextEdit, QMessageBox
)
import string

class TestingProcess():
    def __init__(self, arduino_port, file_path=None):
        """
        Initializes connections to both the Arduino and the DMM based on the selected USB ports.
        """
        self.arduino_port = arduino_port
        
        self.file_path = file_path 
        
        self.voltage_per_index = 7.843

        # Initialize Arduino connection
        try:
            self.serial_file = open_serial_port(arduino_port, baudrate=115200, timeout=None)
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Arduino on {arduino_port}: {e}")

        is_connected = False
        while not is_connected:
            print("Waiting for Arduino...")
            write_order(self.serial_file, Order.HELLO)

            bytes_array = bytearray(self.serial_file.read(1))
            if not bytes_array:
                time.sleep(2)
                continue

            byte = bytes_array[0]
            if byte in [Order.HELLO.value, Order.ALREADY_CONNECTED.value]:
                is_connected = True
                write_order(self.serial_file, Order.ALREADY_CONNECTED)

        print(f"Connected to Arduino on {arduino_port}")
        
    def standardTest(self):
        for i in range(100,255):
            print(f"Step: {i}")
            write_order(self.serial_file, Order.HV_SET,i)
            bytes_array = bytearray(self.serial_file.read(1))
            time.sleep(0.1)
            if not bytes_array:
                print("Nothing recieved")
            else:
                print("maybe yay")
            time.sleep(10)
            
        self.serial_file.close()    


if __name__ == "__main__":
    arduino_port = "/dev/ttyACM0"  # Example port, replace with actual selection
    #dmm_port = "USB0::0x1AB1::0x09C4::DM3R12345678::INSTR"  # Example VISA address

    tester = TestingProcess(arduino_port)
    tester.standardTest()
