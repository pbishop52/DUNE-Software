import time
import os
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
from PyQt5.QtCore import QObject, pyqtSignal
import string

TARGET_RESISTANCE = 5000e6  # 5000 MΩ
BIN_PERCENT_STEP = 0.002    # 0.2%
BIN_RANGE = 0.01            # ±1.0%
BIN_LABELS = list(string.ascii_uppercase)

# Step 1: Define range and calculate edges
range_steps = int(BIN_RANGE / BIN_PERCENT_STEP)
edges = [TARGET_RESISTANCE * (1 + i * BIN_PERCENT_STEP) for i in range(-range_steps, range_steps + 1)]

# Step 2: Sort edges by distance to center (TARGET_RESISTANCE)
sorted_edges = sorted(edges, key=lambda x: abs(x - TARGET_RESISTANCE))

# Step 3: Map sorted edges to bin labels
bin_edges = sorted_edges
label_map = {edge: BIN_LABELS[i] for i, edge in enumerate(bin_edges)}

def bin_resistance(value):
    diffs = [abs(value - edge) for edge in bin_edges]
    idx = int(np.argmin(diffs))
    return BIN_LABELS[idx]


class TestingProcess(QObject):
    relay_updated = pyqtSignal(int)
    voltage_measured = pyqtSignal(float, float, float)
    voltage_live = pyqtSignal(float)
    test_complete = pyqtSignal()

    def __init__(self, arduino_port, dmm_port, file_path=None):
        """
        Initializes connections to both the Arduino and the DMM based on the selected USB ports.
        """
        super().__init__()
        self.arduino_port = arduino_port
        self.dmm_port = dmm_port
        self.file_path = file_path
        self.is_running = True
        self.data = []
        self.test_info = {}
        

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
            
       
    def set_test_info(self, info_dict):
        self.test_info = info_dict  
        self.timestamp = int(time.time())
        
    def build_csv_path(self, folder_path):
        if hasattr(self, 'test_info') and hasattr(self, 'timestamp'):
            filename = f"WM_Comp_test_{self.test_info['Stand Number']}_{self.test_info['Dunk Board']}_{self.timestamp}.csv"
            self.file_path = os.path.join(folder_path, filename)
            
       
    def save_data_csv(self):
        if self.file_path and self.data:
            try:
                with open(self.file_path, 'w', newline = '') as csvfile:
                    writer =csv.writer(csvfile)
                    
                    writer.writerow(["ID:", f"{self.test_info['Stand Number']}_{self.test_info['Dunk Board']}_{self.timestamp}", "User:", self.test_info['Tester Name']])
                    
                    writer.writerow(["Calibration Channel (-1 if not calib):", self.test_info['Calib Channel'], "Calibration Value (GOhm):",self.test_info['Calib Value']])
                    
                    writer.writerow(['HV Index', 'CHANNEL', 'Voltage','Error'])
                    
                    for row in self.data:
                        writer.writerow([row['DAC Value'],row['Relay'],row['Measured Voltage [V]'], row['Voltage Error [V]']])
                    print(f"Data saved successfully to {self.file_path}")
            except Exception as e:
                print(f"Error saving CSV: {e}")
                    
                    
            
                    
    
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
            
    def DMM_live_readings(self, input_HV):
        
        readings = []
        for _ in range(10):
            if not self.is_running:
                print("Test cancelled during DMM read.")
                return None, None
                
                
            voltage = self.read_DMM()
            if voltage is not None:
                readings.append(voltage)
                self.voltage_live.emit(voltage)
            time.sleep(0.5)  # Small delay between readings
        return readings
            
            

    def communicate_with_DMM(self, readings):
        """
        Polls data from the digital multimeter (DMM), averages over 10 readings,
        and calculates standard error.
        """
        
        if len(readings) > 0:
            avg_voltage = np.mean(readings)
            std_err = np.std(readings)
            return avg_voltage, std_err
        else:
            return None, None

    def stop(self):
        print("TestingProcess: Stopping Test.")
        if not self.is_running:
            return
        
        try:
            print("Setting HV to 0")
            write_order(self.serial_file, Order.HV_SET,0)
            time.sleep(2)
            self.serial_file.read(1)
            
            print("opening all relays")
            for relay in range(8):
                write_order(self.serial_file, Order.OPEN_RELAYS)
                time.sleep(0.1)
                self.serial_file.read(1)
                
        except Exception as e:
            print("Error during stop cleanup: {e}")
        
        if self.data:
            self.save_data_csv()
        if hasattr(self, 'serial_file') and self.serial_file:
            self.serial_file.close()
        
        self.test_complete.emit()
            
        
        
    def standardTest(self):
        step_size = 13 #DAC units for ~100V step
        low_index = 0
        upper_index = 256
        voltage_per_unit = 7.843 # = 2000/255
        num_relays = 8
        #data = []
        
        
        print(f"Step size = {step_size}, approx 100V step size")
        for i in range(low_index,upper_index,step_size):
            input_HV = i*voltage_per_unit
            
            
            if not self.is_running:
                self.stop()
                return
                #break
                
                
            print(f"Setting HV to DAC value: {i} ~ {input_HV:.2f} V")
            write_order(self.serial_file, Order.HV_SET,i)
            time.sleep(2)
            self.serial_file.read(1)
            
            bytes_array = bytearray(self.serial_file.read(1))
            if not bytes_array:
                print("No HV order received")
            else:
                print(f"Arduino communicating")
            
            for relay in range(num_relays):
                
                if not self.is_running:
                    self.stop()
                    return
                    #break
                  
                print(f"Activating relay {relay+1} at {input_HV:.2f} V")
                write_order(self.serial_file, Order.RELAY, relay)
                self.relay_updated.emit(relay)
                self.serial_file.read(1)
                
                
                
                relay_array = bytearray(self.serial_file.read(1))
                if not relay_array:
                    print("No RELAY order received")
                else:
                    print(f"Relay {relay +1} activated")
                    
                    readings = self.DMM_live_readings(input_HV)
                    avg_voltage, std_err = self.communicate_with_DMM(readings)
                    
                    if avg_voltage is not None:
                        #self.relay_updated.emit(relay)
                        self.voltage_measured.emit(avg_voltage, std_err, input_HV)

                        print(f" {avg_voltage:.4f} +- {std_err:.4f} V measured across relay {relay+1}")
                        self.data.append({'DAC Value': i, 'Voltage Step [V]': i*voltage_per_unit, 'Relay': relay+1, 'Measured Voltage [V]': avg_voltage, 'Voltage Error [V]': std_err})
                    else:
                        print(f"Failed to get DMM reading for relay {relay +1}")
                    
                    
                    
                    time.sleep(5)
            
            #response = input("Type y to continue to next stage, anything else to quit:  ").strip().lower()
            #if response != 'y':
                #print("Stopping test.")
                #break
        self.save_data_csv()
        self.test_complete.emit()
        self.serial_file.close()
        self.stop()


if __name__ == "__main__":
    arduino_port = "/dev/ttyACM0"  # Example port, replace with actual selection
    dmm_port = "USB0::62700::4609::SDM35HBC800947::0::INSTR"  # Example VISA address

    tester = TestingProcess(arduino_port, dmm_port)
    tester.standardTest()
