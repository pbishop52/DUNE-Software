import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, \
    QTableWidgetItem
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer
import matplotlib.pyplot as plt


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Set up the main layout
        self.main_layout = QHBoxLayout(self)

        # Create the tab widget with three tabs
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()

        self.tabs.addTab(self.tab1, "Tab 1")
        self.tabs.addTab(self.tab2, "Tab 2")
        self.tabs.addTab(self.tab3, "Tab 3")

        # Add a table to Tab 1
        self.setupTab1()

        # Set up tabs for plot labels (optional)
        self.setupTab(self.tab2, "Plot 2")
        self.setupTab(self.tab3, "Plot 3")

        # Layout for the tab widget
        tab_layout = QVBoxLayout()
        tab_layout.addWidget(self.tabs)
        tab_container = QWidget()
        tab_container.setLayout(tab_layout)

        # Add the tab container to the main layout
        self.main_layout.addWidget(tab_container)

        # Create image labels and add them to the right of the tab widget
        self.image_layout = QVBoxLayout()
        self.image_labels = []  # Store references to image labels
        self.image_paths = ['plot1.png', 'plot2.png', 'plot3.png']  # Define paths to the plot images
        self.streamed_data = [[], [], []]  # Lists to store the streaming data for each plot

        for i, image_path in enumerate(self.image_paths):
            label = QLabel(self)
            pixmap = QPixmap(image_path)  # Load initial images if available
            label.setPixmap(pixmap.scaled(100, 100))  # Adjust size as needed
            self.image_layout.addWidget(label)
            self.image_labels.append(label)

        # Add the image layout to the main layout
        self.main_layout.addLayout(self.image_layout)

        # Set up a timer to update plots and images based on the data stream
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updatePlots)
        self.timer.start(1000)  # Update every 1000 ms (1 second)

    def setupTab1(self):
        """ Sets up Tab 1 with a table to display plot values """
        layout = QVBoxLayout()

        # Create a table to display the last 10 data points for each plot
        self.table = QTableWidget()
        self.table.setRowCount(10)  # Show the last 10 data points
        self.table.setColumnCount(3)  # One column for each plot
        self.table.setHorizontalHeaderLabels(["Plot 1", "Plot 2", "Plot 3"])

        layout.addWidget(self.table)
        self.tab1.setLayout(layout)

    def setupTab(self, tab, title_text):
        """ Helper function to set up a tab with a label """
        layout = QVBoxLayout()
        label = QLabel(title_text)
        layout.addWidget(label)
        tab.setLayout(layout)

    def updatePlots(self):
        """ Generates new random data points, updates the plots, and updates the table """
        for i in range(len(self.image_paths)):
            # Simulate receiving a new data point for each plot
            new_data_point = random.randint(1, 10)
            self.streamed_data[i].append(new_data_point)

            # Limit data points to the latest 10 values to simulate a "sliding window" of data
            if len(self.streamed_data[i]) > 10:
                self.streamed_data[i].pop(0)

            # Generate and update the plot with the streamed data
            self.generatePlot(i)

            # Update the corresponding image in the GUI
            pixmap = QPixmap(self.image_paths[i])
            self.image_labels[i].setPixmap(pixmap.scaled(100, 100))

        # Update the table with the latest data
        self.updateTable()

    def generatePlot(self, plot_index):
        """ Generates a plot based on the current streamed data and saves it as an image file """
        # Get the current data for this plot
        y = self.streamed_data[plot_index]
        x = list(range(len(y)))  # X-axis is just the index of each data point

        # Create the plot
        plt.figure()
        plt.plot(x, y, marker='o')
        plt.title(f"Streaming Plot {plot_index + 1}")
        plt.xlabel("Time")
        plt.ylabel("Value")

        # Save the plot to the corresponding image path
        plot_path = self.image_paths[plot_index]
        plt.savefig(plot_path)
        plt.close()

    def updateTable(self):
        """ Updates the table in Tab 1 with the latest data from each plot """
        for col, data in enumerate(self.streamed_data):
            # Fill each column with the last 10 data points, or empty cells if fewer than 10
            for row in range(10):
                if row < len(data):
                    item = QTableWidgetItem(str(data[row]))
                else:
                    item = QTableWidgetItem("")
                self.table.setItem(row, col, item)


# Run the application
app = QApplication(sys.argv)
mainWin = MainWindow()
mainWin.setWindowTitle("PyQt5 Streaming Plots with Table Display")
mainWin.resize(800, 400)
mainWin.show()
sys.exit(app.exec_())
