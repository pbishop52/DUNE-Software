import glob
import queue
import sys
from typing import List, Optional

import serial
import serial.tools.list_ports

# From https://stackoverflow.com/questions/6517953/clear-all-items-from-the-queue
class CustomQueue(queue.Queue):
    """
    A custom queue subclass that provides a :meth:`clear` method.
    """

    def clear(self) -> None:
        """
        Clears all items from the queue.
        """

        with self.mutex:
            unfinished = self.unfinished_tasks - len(self.queue)
            if unfinished <= 0:
                if unfinished < 0:
                    raise ValueError("task_done() called too many times")
                self.all_tasks_done.notify_all()
            self.unfinished_tasks = unfinished
            self.queue.clear()
            self.not_full.notify_all()


# From https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python
def get_serial_ports() -> List[str]:
    """
    Lists serial ports.


    :return: A list of available serial ports
    """


    available_ports = list(serial.tools.list_ports.comports())

    for i in range(len(available_ports)-1):

        port=available_ports[i]

        if "Arduino"  not in port.description:

            available_ports.remove(port)



    results = []


    for port in available_ports:

        try:
            s = serial.Serial(port.device)
            s.close()
            results.append(port.device)
        except (OSError, serial.SerialException):
            pass
    return results


def open_serial_port(
    serial_port: Optional[str] = None,
    baudrate: int = 115200,
    timeout: Optional[int] = 0,
    write_timeout: int = 0,
) -> serial.Serial:
    """
    Try to open serial port with Arduino
    If not port is specified, it will be automatically detected

    :param serial_port:
    :param baudrate:
    :param timeout: None -> blocking mode
    :param write_timeout:
    :return: (Serial Object)
    """
    # Open serial port (for communication with Arduino)
    if serial_port is None:
        serial_port = get_serial_ports()[0]
    # timeout=0 non-blocking mode, return immediately in any case, returning zero or more,
    # up to the requested number of bytes
    return serial.Serial(port=serial_port, baudrate=baudrate, timeout=timeout, writeTimeout=write_timeout)

def setRelay(serial_conn, current_relay: int) -> None:
    """
    Opens all relays, then closes only the selected relay.

    :param serial_conn: Serial connection object
    :param current_relay: The relay to be closed (activated)
    """
    # Open (deactivate) all relays
    for relay in range(10):  # Assuming 10 relays (adjust if needed)
        write_order(serial_conn, Order.RELAY, relay)
    
    # Close (activate) the current relay
    write_order(serial_conn, Order.RELAY, current_relay)

    print(f"Relay {current_relay} activated.")