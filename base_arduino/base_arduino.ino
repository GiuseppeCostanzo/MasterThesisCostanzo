#include <Servo.h>

// Servo definitions
Servo thumb;
Servo index_finger;
Servo middle_finger;
Servo ring_finger;
Servo pinky;
Servo forearm;

String inByte;
//int pos;
int receivedData[6];

void setup() {
  Serial.begin(9600);

  // communication pin for each servo
  thumb.attach(3);
  index_finger.attach(5);
  middle_finger.attach(6);
  ring_finger.attach(9);
  pinky.attach(10);
  forearm.attach(11);

  //initial position of each servo
  thumb.write(90);
  index_finger.write(90);
  middle_finger.write(90);
  ring_finger.write(90);
  pinky.write(90);
  forearm.write(90); 
}

void loop() {
  // if data available in serial port
  if (Serial.available()){
    for (int i = 0; i < 6; i++) {
      //Serial.print(" ");
      receivedData[i] = Serial.read();
      //Serial.print(receivedData[i]);
      //Serial.print(" ");
    }
    thumb.write(receivedData[0]);
    index_finger.write(receivedData[1]);
    middle_finger.write(receivedData[2]);
    ring_finger.write(receivedData[3]);
    pinky.write(receivedData[4]);
    forearm.write(receivedData[5]); 

  }
}