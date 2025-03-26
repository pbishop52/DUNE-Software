import sys
import csv
import time
from PyQt5.QtWidgets import QApplication
from gui import ResistorTestGUI
from testingprocess import TestingProcess

class MainApp:
    def __init__(self):
        self.testing_process = TestingProcess()
        self.app = QApplication(sys.argv)
        self.gui = ResistorTestGUI()
        self.gui.start_test_signal.connect(self.start_test)
        self.gui.stop_test_signal.connect(self.stop_test)
        self.is_running = False
        
    def start_test(self, file_path):
        if self.is_running:
            return
        self.is_running = True
        self.file_path = file_path
        self.run_test()

    def stop_test(self):
        self.is_running = False
        self.testing_process.stop_testing()
        self.gui.append_log("Testing stopped.")

    def run_test(self):
        self.gui.append_log("Starting resistor test...")
        data = []
        
        for voltage_stage, relay, voltage, std_err in self.testing_process.standardTest():
            if not self.is_running:
                break
            timestamp = time.time()
            self.gui.update_plot(timestamp, voltage)
            self.gui.update_active_relay(relay)
            data.append([timestamp, voltage_stage, relay, voltage, std_err])
            self.gui.append_log(f"Relay {relay} - Voltage: {voltage:.2f}V, Std Err: {std_err:.2f}")
        
        self.save_data(data)
        self.gui.append_log("Testing complete. Data saved.")
        self.is_running = False

    def save_data(self, data):
        if not self.file_path:
            return
        with open(self.file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Voltage Stage", "Relay", "Voltage", "Std Err"])
            writer.writerows(data)
        self.gui.append_log(f"Data saved to {self.file_path}")

    def run(self):
        self.gui.show()
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    main_app = MainApp()
    main_app.run()
