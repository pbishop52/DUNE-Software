# DUNE Component Testing Software
Hello! Here houses the some of the code I created alongside Robin James for DUNE resistor and varistor testing while working at William & Mary. 
## Table of Contents
- [Overview](#overview)
- [File and Modules Descriptions](#file-and-modules-descriptions)
## Overview
This project was made in need for a software side of the testing procedure for DUNE. This architecture was made to automate testing and analysis for DUNE. I created the testing procedure, GUI, and various GUI popups and inputs. Robin James created the Test PCBs, the Arduino code, and found the robust serial communication framework. Code is run locally at William & Mary and is pushed/pulled from WM-Robin Organization on Github. Here is copy of the repository, updated as of 7/10/2025.
## File and modules descriptions
* arduino - Houses the code for the arduino, including its side of the communication system
* robust_serial- Computer side of the communication system, derived from https://github.com/araffin/arduino-robust-serial/tree/master
  * utils.py- Contain helper functions for working with the serial port
  * robust_serial.py- Bulk of the custom communication protocol including definition of orders, functions to send orders ,and 
  decoding messages
* main.py - Launches the GUI and runs the testing procedure, still needs to be edited.
* TestProc01.py - This is where the testing procedure is defined and communicating with the GUI framework. 
* gui_test.py - GUI display for testing procedure. Communicates with TestProc01 to go through defined procedure for DUNE testing. Created using PyQT5.
* TestProc_old.py - Older iteration of testing procedure before standardized saving format was made.
* TestProcedureCLI.py - Testing process created for the sole purpose of performing testing in the CLI, skipping the GUI communication entirely.
* PreTestPopup.py - GUI popup that prompts user to enter pertinent test information, such as name, test number, board number, temp, etc.
  
