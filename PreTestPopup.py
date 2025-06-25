from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QLabel, QPushButton

class TestDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pre Test Information")
        
        self.layout = QVBoxLayout()
        
        self.name_label = QLabel("Tester Name:")
        self.name_input = QLineEdit()
        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.name_input)
        
        self.test_num_label = QLabel("Test Number:")
        self.test_num_input = QLineEdit()
        self.layout.addWidget(self.test_num_label)
        self.layout.addWidget(self.test_num_input)
        
        self.stand_num_label = QLabel("Stand Number:")
        self.stand_num_input = QLineEdit()
        self.layout.addWidget(self.stand_num_label)
        self.layout.addWidget(self.stand_num_input)
        
        self.dunk_board_label = QLabel("Dunk Board:")
        self.dunk_board_input = QLineEdit()
        self.layout.addWidget(self.dunk_board_label)
        self.layout.addWidget(self.dunk_board_input)
        
        self.calib_channel_label = QLabel("Calib Channel (-1 if none):")
        self.calib_channel_input = QLineEdit()
        self.layout.addWidget(self.calib_channel_label)
        self.layout.addWidget(self.calib_channel_input)
        
        self.calib_value_label = QLabel("Calib Value (GOhm):")
        self.calib_value_input = QLineEdit()
        self.layout.addWidget(self.calib_value_label)
        self.layout.addWidget(self.calib_value_input)
        
        self.temp_label = QLabel("Temperature in degree C:")
        self.temp_input = QLineEdit()
        self.layout.addWidget(self.temp_label)
        self.layout.addWidget(self.temp_input)
        
        self.ok_button = QPushButton("Ok")
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)
        
        self.setLayout(self.layout)
        
        
    def validate_inputs(self):
        name = self.name_input.text().strip()
        test_num = self.test_num_input.text().strip()
        temp = self.temp_input.text().strip()
        
        stand_num = self.stand_num_input.text().strip()
        dunk_board = self.dunk_board_input.text().strip()
        calib_channel = self.calib_channel_input.text().strip()
        calib_value= self.calib_value_input.text().strip()
        
        
        if not name:
            QMessageBox.warning(self, "Input Error", "Tester name cannot be empty.")
            return
            
            
        if not test_num.isdigit():
            QMessageBox.warning(self, "Input Error", "Test number must be an integer.")
            return
            
        if not stand_num.isdigit():
            QMessageBox.warning(self, "Input Error", "Stand number must be an integer.")
            return
            
        if not dunk_board.isdigit():
            QMessageBox.warning(self, "Input Error", "Dunk Board must be an integer.")
            return
            
        if not calib_channel.isdigit():
            QMessageBox.warning(self, "Input Error", "Test number must be an integer.")
            return
            
            
        try:
            float(calib_value)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "calib_value must be a number.")
            return
            
            
        try:
            float(temp)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Temperature must be a number.")
            return
        
        self.accept()
    
    def input_vals(self):
        return{
            'Tester Name': self.name_input.text(),
            'Test Number': self.test_num_input.text(),
            'Stand Number': self.stand_num_input.text(),
            'Dunk Board': self.dunk_board_input.text(),
            'Calib Channel': self.calib_channel_input.text(),
            'Calib Value': self.calib_value_input.text(),
            'Temperature': self.temp_input.text()
        }
        
