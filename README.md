# DUNE Component Testing Software

## File and modules descriptions

* arduino - Houses the code for the arduino, including its side of the communication system
  * TODO
* robust_serial- Computer side of the communication system, derived from https://github.com/araffin/arduino-robust-serial/tree/master
  * utils.py- Contain helper functions for working with the serial port
  * robust_serial.py- Bulk of the custom communication protocol including definition of orders, functions to send orders ,and 
  decoding messages
* main.py- Start of the code, currently has code to initials connection to the arduino and looping through the relays 
* testingProcess.py - This is where the code to run the test and collect data is housed
* DuneTestWidget.py- GUI for testing process, currently has code I was playing around with tabs and updating plots live.
  