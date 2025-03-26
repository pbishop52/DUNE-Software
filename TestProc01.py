import time
import csv
import numpy as np
import pyvisa
from time import sleep
from robust_serial import Order, read_order, write_i8, write_i16, write_order
from utils import open_serial_port, setRelay  # Import setRelay function

class TestingProcess():
    def __init__(self):
        try:
            self.serial_file = open_serial_port(baudrate=115200, timeout=None)
        except Exception as e:
            raise e

        is_connected = False
        # Initialize communication with Arduino
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

        print("Connected to Arduino")

    def communicate_with_DMM(self):
        """
        Polls data from the digital multimeter (DMM), averages over 10 readings, 
        and calculates standard error.
        """
        readings = []
        for _ in range(10):
            voltage = self.read_DMM()  # Replace with actual DMM reading function
            readings.append(voltage)
            time.sleep(0.5)  # Small delay between readings
        
        avg_voltage = np.mean(readings)
        std_err = np.std(readings, ddof=1) / np.sqrt(len(readings))  # Standard Error
        
        return avg_voltage, std_err

    def read_DMM(self):
        """
        Placeholder for actual DMM communication. Replace this with actual code 
        to fetch voltage from digital multimeter via USB.
        """
        return np.random.uniform(0, 10)  # Simulated voltage reading

    def standardTest(self, hvLimit=2000, samplesPerStage=10, voltageStages=19, 
                     voltagePerIndex=7.843, lowVoltage=100, numRelays=8):
        """
        Conducts the testing process through multiple voltage steps and relay switches.
        """
        # Generate high voltage steps
        indexLimit = int(hvLimit // voltagePerIndex)
        lowIndex = int(lowVoltage // voltagePerIndex)
        stages_index = range(lowIndex, indexLimit, int((indexLimit - lowIndex) // samplesPerStage))

        # Prepare CSV file to save results
        with open("test_results.csv", "w", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["Voltage Step", "Relay", "Avg Voltage (V)", "Standard Error"])

            # Iterate through voltage steps
            for voltageStage in stages_index:
                print(f"Setting high voltage to stage {voltageStage}")
                write_order(self.serial_file, Order.HV_UPDATED)  # Order 12

                # Confirm high voltage update
                while read_order(self.serial_file) != Order.HV_UPDATED:
                    time.sleep(0.1)

                # Iterate through all relays
                for relay in range(numRelays):
                    print(f"Closing relay {relay}")
                    setRelay(self.serial_file, relay)  # Close relay
                    write_order(self.serial_file, Order.READY_RELAY)  # Order 8

                    # Confirm relay is ready
                    while read_order(self.serial_file) != Order.READY_RELAY:
                        time.sleep(0.1)

                    # Read voltage data from DMM
                    avg_voltage, std_err = self.communicate_with_DMM()
                    print(f"Relay {relay}: Avg Voltage = {avg_voltage:.3f} V, Std Err = {std_err:.3f} V")

                    # Send data update order to Arduino
                    write_order(self.serial_file, Order.DATA_UPDATE)  # Order 11

                    # Save data to CSV
                    csv_writer.writerow([voltageStage, relay, avg_voltage, std_err])

            print("Testing complete. Turning off high voltage.")
            write_order(self.serial_file, Order.HV_UPDATED)  # Order to turn off HV

        print("Data saved to test_results.csv")


# Example Usage
if __name__ == "__main__":
    tester = TestingProcess()
    tester.standardTest()
