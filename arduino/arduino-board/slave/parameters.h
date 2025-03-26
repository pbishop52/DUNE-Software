#ifndef PARAMETERS_H
#define PARAMETERS_H

#define SERIAL_BAUD 115200  // Baudrate

#define DIRECTION_PIN 9
#define stepPin 10

#define SPEED_MAX 100

// If DEBUG is set to true, the arduino will send back all the received messages
#define DEBUG false

static int RELAY_CHANNEL[8] = {2,4,5,6,7,8,12,13}; 
// steper pins 9, 10
#define HV_CONTROL 3

#endif
