import time
import sys
from time import sleep

from robust_serial import Order, read_order, write_i8, write_i16, write_order
from robust_serial.utils import open_serial_port


class TestingProcess():
    Serial_file=None
    def __init__(self):

        try:
            serial_file = open_serial_port(baudrate=115200, timeout=None)
        except Exception as e:
            raise e

        is_connected = False
        # Initialize communication with Arduino
        while not is_connected:
            print("Waiting for arduino...")
            write_order(serial_file, Order.HELLO)

            bytes_array = bytearray(serial_file.read(1))

            if not bytes_array:
                time.sleep(2)
                continue
            byte = bytes_array[0]
            if byte in [Order.HELLO.value, Order.ALREADY_CONNECTED.value]:
                is_connected = True
                write_order(serial_file, Order.ALREADY_CONNECTED)

        print("Connected to Arduino")

    def standardTest(self,hvLimit=2000, samplesPerStage=10, voltageStages=19, voltagePerIndex=7.843, lowVoltage=100):

        ## Generate HV steps
        indexLimit= int(hvLimit // voltagePerIndex)
        lowIndex = int(lowVoltage // voltagePerIndex)
        stagesindex=range(lowIndex,indexLimit, int((indexLimit-lowIndex)//samplesPerStage))
        # iterate through voltage steps
        for voltageStage in stagesindex:


            return