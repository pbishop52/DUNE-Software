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
    def __init__(self, arduino_port, dmm_port, file_path=None):
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
        
        self.rm = pyvisa.ResourceManager()
        try:
            self.dmm = self.rm.open_resource(dmm_port)
            self.dmm.write("*IDN?")
            self.dmm.timeout = 5000
            self.dmm.write_termination = '\n'
            self.dmm.read_termination = '\n'
            print(f"Connected to DMM on {dmm_port}")
        except Exception as e:
            raise RuntimeError(f"failed to connect to dmm on {dmm_port}")
    def read_DMM(self):
        """
        Reads voltage from the Siglent SDM3055 digital multimeter via USB.
        """
        try:
            voltage = float(self.dmm.query("MEAS:VOLT:DC?"))
            return voltage
        except Exception as e:
            print(f"Error reading from DMM: {e}")
            return None  # Return None if reading fails

    def communicate_with_DMM(self):
        """
        Polls data from the digital multimeter (DMM), averages over 10 readings,
        and calculates standard error.
        """
        readings = []
        for _ in range(10):
            voltage = self.read_DMM()
            if voltage is not None:
                readings.append(voltage)
            time.sleep(0.5)  # Small delay between readings
        
        if len(readings) > 0:
            avg_voltage = np.mean(readings)
            std_err = np.std(readings, ddof=1) / np.sqrt(len(readings))  # Standard Error
            return avg_voltage, std_err
        else:
            return None, None

       
    def standardTest(self):
        step_size = 13 #DAC units for ~100V step
        low_index = 0
        upper_index = 256
        voltage_per_unit = 7.843 # = 2000/255
        num_relays = 8
        
        
        print(f"Step size = {step_size}, approx 100V step size")
        for i in range(low_index,upper_index,step_size):
            #print(f"Step: {i}")
            print(f"Setting HV to DAC value: {i} ~ {i * voltage_per_unit:.2f} V")
            
            write_order(self.serial_file, Order.HV_SET,i)
            time.sleep(0.1)
            
            bytes_array = bytearray(self.serial_file.read(1))
            if not bytes_array:
                print("No HV order received")
            else:
                print(f"Arduino communicating")
            
            for relay in range(num_relays):
                print(f"Activating relay {relay} at {i * voltage_per_unit:.2f} V")
                write_order(self.serial_file, Order.RELAY, relay)
                
                relay_array = bytearray(self.serial_file.read(1))
                if not relay_array:
                    print("No RELAY order received")
                else:
                    print(f"Relay {relay} activated")
                
                
            
            response = input("Type y to continue to next stage, anything else to quit:  ").strip().lower()
            if response != 'y':
                print("Stopping test.")
                break
            
            
        self.serial_file.close()    


if __name__ == "__main__":
    arduino_port = "/dev/ttyACM0"  # Example port, replace with actual selection
    dmm_port = "USB0::62700::4609::SDM35HBC800947::0::INSTR"  # Example VISA address

    tester = TestingProcess(arduino_port, dmm_port)
    tester.standardTest()
