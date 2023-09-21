#include <Servo.h>

// Definizione dei servomotori
Servo thumb;
Servo index_finger;
Servo middle_finger;
Servo ring_finger;
Servo pinky;
Servo forearm;

String inByte;
int pos;

void setup() {
  Serial.begin(9600);
  index_finger.attach(9);
}

void loop() {
  if (Serial.available())  // if data available in serial port
  {
    inByte = Serial.readStringUntil('\n');  // read data until newline
    pos = inByte.toInt();                   // change datatype from string to integer
    index_finger.write(pos);                     // move servo
    //Serial.print("Servo in position: ");
    //Serial.println(inByte);
  }
}