import pyvisa
'''
rm = pyvisa.ResourceManager()
resources = rm.list_resources()

if resources:
    print("Available VISA resources:")
    for res in resources:
        print(F" {res}")
else:
    print("No VISA resources found")
'''
'''
with open("/dev/usbtmc1", "wb+") as f:
    f.write(b"*IDN?\n")
    f.flush()
    response = f.read(1024)
    print(response.decode())
'''
rm = pyvisa.ResourceManager('@py')
dmm = rm.open_resource("USB0::62700::4609::SDM35HBC800947::0::INSTR")
print(dmm.query("*IDN?"))
print(dmm.query("MEAS:VOLT:DC?"))

               '''
                #print(f"Setting high voltage to stage {voltageStage}")

                # Wait for user to manually set the high voltage
                user_confirmed = QMessageBox.question(
                    None, "Manual High Voltage Adjustment", 
                    f"Please set the high voltage to {voltageStage * voltagePerIndex:.2f} V and click OK.",
                    QMessageBox.Ok | QMessageBox.Cancel
                )

                if user_confirmed == QMessageBox.Cancel:
                    print("Test aborted by user.")
                    break  # Exit test if the user cancels

                write_order(self.serial_file, Order.HV_UPDATED)  # Order 12

                # Confirm high voltage update from Arduino
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
                '''
