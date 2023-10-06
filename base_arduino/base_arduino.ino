#include <Servo.h>

// Servo definitions
Servo thumb;
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
  thumb.attach(9);
  index_finger.attach(6);
  middle_finger.attach(10);
  ring_pinky.attach(5);
  forearm.attach(3);

  //initial position of each servo
  //thumb.write(35);
  //index_finger.write(90);
  //middle_finger.write(90);
  //ring_finger.write(90);
  //pinky.write(90);
  //forearm.write(90); 
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


  if(i >= 6){
    Serial.print("Letti 6 valori$");
    thumb.write(receivedData[0]);
    index_finger.write(receivedData[1]);
    middle_finger.write(receivedData[2]);
    ring_pinky.write(receivedData[3]);
    forearm.write(receivedData[4]); 
    }
  }
  // if data available in serial port
  /*if (Serial.available() > 0){
    Serial.print("Qualcosa available$ ");
    for (int i = 0; i < 6; i++) {
      receivedData[i] = Serial.read();
    }*/

}