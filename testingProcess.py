import time
import csv
import numpy as np
import pyvisa
from time import sleep
from robust_serial import Order, read_order, write_i8, write_i16, write_order
from robust_serial.utils import open_serial_port, setRelay  # Import setRelay function

class TestingProcess():
    def __init__(self, arduino_port, dmm_port):
        """
        Initializes connections to both the Arduino and the DMM based on the selected USB ports.
        """
        self.arduino_port = arduino_port
        self.dmm_port = dmm_port

        # Initialize Arduino connection
        try:
            self.serial_file = open_serial_port(port=arduino_port, baudrate=115200, timeout=None)
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
            self.dmm.write("*IDN?")  # Test command to verify connection
            print(f"Connected to DMM on {dmm_port}")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to DMM on {dmm_port}: {e}")

    def read_DMM(self):
        """
        Reads voltage from the Siglent SDM3055 digital multimeter via USB.
        """
        try:
            self.dmm.write("MEAS:VOLT:DC?")  # Command to read DC voltage
            voltage = float(self.dmm.read())  # Read and convert to float
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
        stages_index = range(lowIndex, indexLimit, int((indexLimit - lowIndex) // samplesPerStage))

        # Prepare CSV file to save results
        with open("test_results.csv", "w", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["Voltage Step", "Relay", "Avg Voltage (V)", "Standard Error","Current (A)", "Resistance (MΩ)" ])

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
                    if avg_voltage is not None:
                        print(f"Relay {relay}: Avg Voltage = {avg_voltage:.3f} V, Std Err = {std_err:.3f} V")

                        # Send data update order to Arduino
                        write_order(self.serial_file, Order.DATA_UPDATE)  # Order 11

                        # Save data to CSV
                        csv_writer.writerow([voltageStage, relay, avg_voltage, std_err])
                    else:
                        print(f"Relay {relay}: Failed to read from DMM.")

            print("Testing complete. Turning off high voltage.")
            write_order(self.serial_file, Order.HV_UPDATED)  # Order to turn off HV

        print("Data saved to test_results.csv")


"""
# Example Usage
if __name__ == "__main__":
    arduino_port = "COM3"  # Example port, replace with actual selection
    dmm_port = "USB0::0x1AB1::0x09C4::DM3R12345678::INSTR"  # Example VISA address

    tester = TestingProcess(arduino_port, dmm_port)
    tester.standardTest()

No longer need to hardcode com connection as it is made via gui drop down


"""