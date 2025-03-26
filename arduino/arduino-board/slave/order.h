#ifndef ORDER_H
#define ORDER_H

// Define the orders that can be sent and received
enum Order {
  HELLO = 0,
  MOTOR = 1,
  RELAY = 2,
  ALREADY_CONNECTED = 3,
  ERROR = 4,
  RECEIVED = 5,
  STOP = 6,
  HV_SET =7,
  READY_RELAY=8,
  START_TEST=9,
  PAUSE_TEST=10,
  DATA_UPDATE=11,
  HV_UPDATED=12
};

typedef enum Order Order;

#endif
