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


class TestingProcess():
    def __init__(self, arduino_port, dmm_port, file_path=None):
        """
        Initializes connections to both the Arduino and the DMM based on the selected USB ports.
        """
        self.arduino_port = arduino_port
        self.dmm_port = dmm_port
        self.file_path = file_path 
        self.final_resistances = {}

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

        # Initialize DMM connection
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

    def standardTest(self, hvLimit=2000, samplesPerStage=10, voltageStages=19, 
                    voltagePerIndex=7.843, lowVoltage=100, numRelays=8):
        """
        Conducts the testing process through multiple voltage steps and relay switches.
        """
        # Generate high voltage steps
        indexLimit = int(hvLimit // voltagePerIndex)
        lowIndex = int(lowVoltage // voltagePerIndex)
        stages_index = np.linspace(lowIndex, indexLimit,samplesPerStage, dtype=int)
        print(f"Voltage index range: {list(stages_index)}")
        relay_resistances = {relay: [] for relay in range(numRelays)}
        print(f"Saving to: {self.file_path}")


        # Prepare CSV file to save results
        with open(self.file_path, "w", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["Voltage Step", "Relay", "Avg Voltage (V)", "Standard Error", "Resistance (MΩ)","Bin Label"])

            # Iterate through voltage steps
            for voltageStage in stages_index:
                print(f"Starting voltage stage index loop {voltageStage} ({voltageStage * voltagePerIndex:.2f} V)")
                yield voltageStage
                print("Sending HV_UPDATED to arduino...")
                
                attempts = 0
                #write_order(self.serial_file, Order.HV_UPDATED)
                write_order(self.serial_file, Order.HV_SET)
                write_i8(self.serial_file, voltageStage)
                while read_order(self.serial_file) != Order.HV_UPDATED:
                    time.sleep(0.1)
                    attempts += 1
                    if attempts > 100:
                        print("[ERROR] Timeout waiting for HV_UPDATED from Arduino")
                print("Arduino acknowledged HV_UPDATED")
                
                for relay in range(numRelays):
                    print(f"Activating relay {relay}")
                    setRelay(self.serial_file, relay)
                    write_order(self.serial_file,Order.READY_RELAY)
                    attempts = 0
                    while read_order(self.serial_file) !=Order.READY_RELAY:
                        time.sleep(0.1)
                        attempts += 1
                        if attempts > 100:
                            print(f"[ERROR] Timeout waiting for READY_RELAY on relay {relay}")
                            return
                    print(f"Relay {relay} ready. Reading DMM.....")
                        
 
                    # Read voltage data from DMM
                    avg_voltage, std_err = self.communicate_with_DMM()
                    if avg_voltage is not None:
                        print(f"Relay {relay}: Avg Voltage = {avg_voltage:.3f} V, Std Err = {std_err:.3f} V")

                        # Send data update order to Arduino
                        write_order(self.serial_file, Order.DATA_UPDATE)  # Order 11

                        # Save data to CSV
                        current = avg_voltage / 1.47e6  # Calculate current based on resistance of 1.47 MΩ
                        resistance = (voltageStage * voltagePerIndex - avg_voltage) / current / 1e6  # Resistance in MΩ
                        relay_resistances[relay].append(resistance * 1e6)  # store in ohms for binning later
                        bin_label = bin_resistance(resistance * 1e6)
                        csv_writer.writerow([voltageStage, relay, avg_voltage, std_err, resistance,bin_label])
                    else:
                        print(f"Relay {relay}: Failed to read from DMM.")

            print("Calculating final resistances ...")
            self.final_resistances = {}  # reset for this run
            for relay, resistances in relay_resistances.items():
                if resistances:
                    avg_res = np.mean(resistances)
                    bin_label = bin_resistance(avg_res)
                    self.final_resistances[relay] = {
                        "avg_resistance": avg_res,
                        "bin_label": bin_label
                    }

            print("Testing complete. Turning off high voltage.")
            write_order(self.serial_file, Order.HV_UPDATED)  # Order to turn off HV

        print("Data saved to test_results.csv")
    def get_final_resistances(self):
        
        return self.final_resistances     


"""
# Example Usage
if __name__ == "__main__":
    arduino_port = "COM3"  # Example port, replace with actual selection
    dmm_port = "USB0::0x1AB1::0x09C4::DM3R12345678::INSTR"  # Example VISA address

    tester = TestingProcess(arduino_port, dmm_port)
    tester.standardTest()

No longer need to hardcode com connection as it is made via gui drop down


"""

