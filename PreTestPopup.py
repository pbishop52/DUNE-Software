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
        
        self.temp_label = QLabel("Temperature in degree C:")
        self.temp_input = QLineEdit()
        self.layout.addWidget(self.temp_label)
        self.layout.addWidget(self.temp_input)
        
        self.ok_button = QPushButton("Ok")
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)
        
        self.setLayout(self.layout)
        
        
    def validate_inputs(self):
        name = self.name_input.text()
        test_num = self.test_num_input.text()
        temp = self.temp_input.text()
        
        if not name:
            QMessageBox.warning(self, "Input Error", "Tester name cannot be empty.")
            return
        if not test_num.isdigit():
            QMessageBox.warning(self, "Input Error", "Test number must be an integer.")
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
            'Test number': self.test_num_input.text(),
            'Temperature': self.temp_input.text()
        }
        
