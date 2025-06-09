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

class RelayTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.relay_grid = QGridLayout()
        self.layout.addLayout(self.relay_grid)

        self.relay_buttons = []
        for i in range(8):  # Assuming 8 relays
            relay_button = QPushButton(f"Relay {i+1}")
            relay_button.setStyleSheet("background-color: gray;")
            self.relay_grid.addWidget(relay_button, i // 4, i % 4)
            self.relay_buttons.append(relay_button)

        self.setLayout(self.layout)

    def update_relay_status(self, active_relay):
        for i, button in enumerate(self.relay_buttons):
            button.setStyleSheet("background-color: green;" if i == active_relay else "background-color: gray;")


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

        self.testing_thread = QThread()
        self.testing_process = TestingProcess(arduino_port, dmm_port, file_path)
        self.testing_process.moveToThread(self.testing_thread)

        self.testing_thread.started.connect(self.testing_process.standardTest)
        self.testing_process.relay_updated.connect(self.relay_tab.update_relay_status)
        self.testing_process.voltage_measured.connect(self.update_voltage_plot)
        self.testing_process.test_complete.connect(self.on_test_complete)
        
        self.testing_process.test_complete.connect(self.testing_thread.quit)
        self.testing_thread.finished.connect(self.testing_process.deleteLater)
        self.testing_thread.finished.connect(self.testing_thread.deleteLater)
        

        self.testing_thread.start()
        self.timer.start(1000)

    def stop_test(self):
        print("Stopping test")
        self.is_testing = False
        self.timer.stop()
        if self.testing_process:
            self.testing_process.stop()

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
        #results = self.testing_process.get_final_resistances()



    def update_voltage_plot(self, avg_voltage, std_err):
        if self.is_testing:
            self.plot_data.append((len(self.plot_data), avg_voltage))
            x, y = zip(*self.plot_data)
            self.plot_curve.setData(x, y)
            


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
