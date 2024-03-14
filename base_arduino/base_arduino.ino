#include <Servo.h>

// Servo definitions
Servo thumb_big;
Servo thumb_little;
Servo index_finger;
Servo middle_finger;
Servo ring_pinky;
Servo forearm;

int i = 0;
//String inByte;
//int pos;
int receivedData[6];

void setup() {
  Serial.begin(9600);

  // communication pin for each servo
  thumb_big.attach(9);
  thumb_little.attach(11);
  index_finger.attach(6);
  middle_finger.attach(10);
  ring_pinky.attach(5);
  forearm.attach(3);

  receivedData[0] = 0;
  receivedData[1] = 0;
  receivedData[2] = 0;
  receivedData[3] = 0;
  receivedData[4] = 0;
  receivedData[5] = 0;

}

void loop() {
  if (Serial.available() > 0) {
    receivedData[i] = Serial.read();
    Serial.print(receivedData[i], DEC);
    Serial.print("&");
    i = i+1;
    }

    // Controlla i servo motori con i valori ricevuti
    thumb_big.write(receivedData[0]);
    thumb_little.write(receivedData[1]);
    index_finger.write(receivedData[2]);
    middle_finger.write(receivedData[3]);
    ring_pinky.write(receivedData[4]);
    forearm.write(receivedData[5]);
  
  // if data available in serial port
  /*if (Serial.available() > 0){
    Serial.print("Qualcosa available$ ");
    for (int i = 0; i < 6; i++) {
      receivedData[i] = Serial.read();
    }
  }*/

}