import sys
import pyvisa
import os
import time
import numpy as np
import serial.tools.list_ports
import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QGridLayout, QComboBox, QFileDialog, QTextEdit, QMessageBox
)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QPainter
from TestProc01 import TestingProcess
from pyqtgraph.exporters import ImageExporter
from PyQt5.QtGui import QPixmap, QPainter

class ResultsWindow(QWidget):
    def __init__(self, results):
        super().__init__()
        self.setWindowTitle("Final Resistance Results")
        self.setGeometry(150, 150, 1000, 250)

        layout = QVBoxLayout()
        row = QHBoxLayout()

        for relay, data in sorted(results.items()):
            relay_container = QWidget()
            relay_container.setFixedWidth(100)
            relay_container.setStyleSheet("""
                QWidget {
                    border: 1px solid #ccc;
                    border-radius: 10px;
                    background-color: #f9f9f9;
                    padding: 10px;
                }
            """)
            relay_layout = QVBoxLayout()
            relay_layout.setAlignment(Qt.AlignTop)
            relay_layout.setSpacing(5)

            relay_label = QLabel(f"<b>Relay {relay}</b>")
            resistance_label = QLabel(f"{data['avg_resistance'] / 1e6:.2f} MΩ")
            bin_label = QLabel(f"Bin: {data['bin_label']}")

            relay_layout.addWidget(relay_label, alignment=Qt.AlignCenter)
            relay_layout.addWidget(resistance_label, alignment=Qt.AlignCenter)
            relay_layout.addWidget(bin_label, alignment=Qt.AlignCenter)

            relay_container.setLayout(relay_layout)
            row.addWidget(relay_container)

        layout.addLayout(row)

        self.save_button = QPushButton("Save as Image")
        self.save_button.clicked.connect(self.save_image)
        layout.addWidget(self.save_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def save_image(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG Files (*.png)")
        if file_path:
            pixmap = self.grab()
            pixmap.save(file_path)
"""
attempt at having a color code
class ResultsWindow(QWidget):
    def __init__(self, results):
        super().__init__()
        self.setWindowTitle("Final Resistance Results")
        self.setGeometry(150, 150, 800, 200)
        layout = QHBoxLayout()

        color_map = {
            "FAIL": "#ff9999",   # Light red
            "WARN": "#fff79a",   # Light yellow
            "PASS": "#b3ffb3"    # Light green
        }

        for relay, data in sorted(results.items()):
            box = QVBoxLayout()
            box_widget = QWidget()
            box_widget.setStyleSheet(f"background-color: {color_map.get(data['bin_label'], '#ffffff')};"
                                     "border: 1px solid black; padding: 10px; border-radius: 5px;")
            inner_layout = QVBoxLayout()
            inner_layout.addWidget(QLabel(f"Relay {relay}"))
            inner_layout.addWidget(QLabel(f"{data['avg_resistance']/1e6:.2f} MΩ"))
            inner_layout.addWidget(QLabel(f"Bin: {data['bin_label']}"))
            box_widget.setLayout(inner_layout)
            box.addWidget(box_widget)
            layout.addLayout(box)

        self.save_button = QPushButton("Save as Image")
        self.save_button.clicked.connect(self.save_image)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

    def save_image(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG Files (*.png)")
        if file_path:
            pixmap = self.grab()
            pixmap.save(file_path)

"""

class RelayTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.relay_grid = QGridLayout()
        self.layout.addLayout(self.relay_grid)

        self.relay_buttons = []
        for i in range(8):  # Assuming 8 relays
            relay_button = QPushButton(f"Relay {i}")
            relay_button.setStyleSheet("background-color: gray;")
            self.relay_grid.addWidget(relay_button, i // 4, i % 4)
            self.relay_buttons.append(relay_button)

        self.setLayout(self.layout)

    def update_relay_status(self, active_relay):
        for i, button in enumerate(self.relay_buttons):
            button.setStyleSheet("background-color: green;" if i == active_relay else "background-color: gray;")

class TestingThread(QThread):
    relay_updated = pyqtSignal(int)
    voltage_stage_prompt = pyqtSignal(float)
    voltage_stage_complete = pyqtSignal()
    voltage_measured = pyqtSignal(float, float)
    test_complete = pyqtSignal()

    def __init__(self,arduino_port, dmm_port, file_path):
        super().__init__()
        self.waiting_for_user = False
        self.testing_process = TestingProcess(arduino_port, dmm_port, file_path)
        self.is_running = True

    def run(self):
        for voltage_stage in self.testing_process.standardTest():
            if not self.is_running:
                return
                
            self.voltage_stage_prompt.emit(voltage_stage)
            self.waiting_for_user = True
            
            while self.waiting_for_user:
                if not self.is_running:
                    return
                time.sleep(0.1)
                
                
            for relay in range(8):
                if not self.is_running:
                    return

                self.relay_updated.emit(relay)
                avg_voltage, std_err = self.testing_process.communicate_with_DMM()
                self.voltage_measured.emit(avg_voltage, std_err)

            self.voltage_stage_complete.emit()
            
        self.test_complete.emit()

    def stop(self):
        self.is_running = False
        
    def resume(self):
        self.waiting_for_user = False
        

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Resistor Testing GUI")
        self.setGeometry(100, 100, 1200, 800)
        self.file_path = ""

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # USB Port Selection
        usb_layout = QHBoxLayout()
        self.arduino_port_dropdown = QComboBox()
        self.dmm_port_dropdown = QComboBox()
        self.refresh_ports()

        usb_layout.addWidget(QLabel("Select Arduino Port:"))
        usb_layout.addWidget(self.arduino_port_dropdown)
        usb_layout.addWidget(QLabel("Select DMM Port:"))
        usb_layout.addWidget(self.dmm_port_dropdown)

        self.refresh_button = QPushButton("Refresh Ports")
        self.refresh_button.clicked.connect(self.refresh_ports)
        usb_layout.addWidget(self.refresh_button)
        main_layout.addLayout(usb_layout)

        # Relay Status Tab
        self.tabs = QTabWidget()
        self.relay_tab = RelayTab()
        self.tabs.addTab(self.relay_tab, "Relay Status")
        main_layout.addWidget(self.tabs)

        # Voltage vs Time Plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setTitle("Voltage vs Time")
        self.plot_widget.setLabel("left", "Voltage (V)")
        self.plot_widget.setLabel("bottom", "Time (s)")
        main_layout.addWidget(self.plot_widget)

        self.plot_data = []
        self.plot_curve = self.plot_widget.plot()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.is_testing = False

        # Start/Stop Buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Test")
        self.stop_button = QPushButton("Stop Test")
        self.start_button.clicked.connect(self.start_test)
        self.stop_button.clicked.connect(self.stop_test)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        main_layout.addLayout(button_layout)

        # File Selection
        file_layout = QHBoxLayout()
        self.file_path_display = QTextEdit()
        self.file_path_display.setReadOnly(True)
        self.file_select_button = QPushButton("Select Save Location")
        self.file_select_button.clicked.connect(self.select_file)

        file_layout.addWidget(self.file_path_display)
        file_layout.addWidget(self.file_select_button)
        main_layout.addLayout(file_layout)

        self.testing_thread = None
        self.testing_process = None
    def update_plot(self):
        """ Updates the plot at regular intervals. """
        if self.is_testing and self.plot_data:
            x, y = zip(*self.plot_data)  # Extract data points
            self.plot_curve.setData(x, y)

    def refresh_ports(self):
        serial_ports = [port.device for port in serial.tools.list_ports.comports()]
        self.arduino_port_dropdown.clear()
        if serial_ports:
            self.arduino_port_dropdown.addItems(serial_ports)
            
        rm = pyvisa.ResourceManager('@py')
        visa_resources = rm.list_resources()
        self.dmm_port_dropdown.clear()
        if visa_resources:
            self.dmm_port_dropdown.addItems(visa_resources)

    def select_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Select File", "", "CSV Files (*.csv)")
        if file_path:
            self.file_path_display.setText(file_path)

    def start_test(self):
        arduino_port = self.arduino_port_dropdown.currentText()
        dmm_port = self.dmm_port_dropdown.currentText()
        file_path = self.file_path_display.toPlainText().strip()


        if not arduino_port or not dmm_port:
            QMessageBox.warning(self, "Error", "Please select both Arduino and DMM ports before starting.")
            return
            
        if not file_path:
            QMessageBox.warning(self, "Error","Please select a file_path to save the test results.")
            return

        self.is_testing = True
        self.plot_data = []

        self.testing_thread = TestingThread(arduino_port, dmm_port, file_path)
        self.testing_process = self.testing_thread.testing_process
        self.testing_thread.relay_updated.connect(self.relay_tab.update_relay_status)
        self.testing_thread.voltage_stage_prompt.connect(self.handle_voltage_stage_prompt)
        self.testing_thread.voltage_measured.connect(self.update_voltage_plot)
        self.testing_thread.test_complete.connect(self.on_test_complete)

        self.testing_thread.start()
        self.timer.start(1000)

    def stop_test(self):
        print("Stopping test")
        self.is_testing = False
        self.timer.stop()
        if self.testing_thread:
            self.testing_thread.waiting_for_user = False
            self.testing_thread.stop()
            self.testing_thread.quit()
            self.testing_thread.wait()

    def on_test_complete(self):
        """Automatically called when testing finishes."""
        self.is_testing = False
        self.timer.stop()

        # Save the voltage vs time plot
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"voltage_vs_time_{timestamp}.png"
        save_path = os.path.join(os.getcwd(), filename)
        exporter = ImageExporter(self.plot_widget.plotItem)
        exporter.export(save_path)
        print(f"Plot saved to {save_path}")

        # Show results summary
        results = self.testing_process.get_final_resistances()
        self.results_window = ResultsWindow(results)
        self.results_window.show()


   #def prompt_voltage_stage(self):
       #QMessageBox.information(self, "Voltage Stage Complete", "Please switch input voltage and click OK to continue.")

    def update_voltage_plot(self, avg_voltage, std_err):
        if self.is_testing:
            self.plot_data.append((len(self.plot_data), avg_voltage))
            x, y = zip(*self.plot_data)
            self.plot_curve.setData(x, y)
            
    def handle_voltage_stage_prompt(self,voltage_Stage):
        voltage_per_index = self.testing_process.voltage_per_index
        
        response = QMessageBox.question(self, "Manual High Voltage Measurement",f"Please set the high voltage to {voltage_Stage * voltage_per_index:.2f} V and click OK.", QMessageBox.Ok | QMessageBox.Cancel)
        
        if response == QMessageBox.Cancel:
            QMessageBoxinformation(self, "Test Aborted", "Test was canceled by the user.")
            self.stop_test()
        else:
            self.testing_thread.resume()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
