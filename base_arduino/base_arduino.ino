#include <Servo.h>

int x; 
Servo thumb_big;
Servo thumb_little;
Servo index_finger;
Servo middle_finger;
Servo ring_pinky;
Servo forearm;
int receivedData[7];
int i = 0;


void setup() { 
	Serial.begin(115200); 
	Serial.setTimeout(1); 
  thumb_big.attach(9);
  thumb_little.attach(11);
  index_finger.attach(6);
  middle_finger.attach(10);
  ring_pinky.attach(5);
  forearm.attach(3);
} 
void loop() { 
	while (Serial.available()){
    i = i+1;
    delay(10);
    receivedData[i] = Serial.readString().toInt(); 
    delay(10);
  } 
  
  if (i>=6){
    i = 0;
    thumb_big.write(receivedData[1]);
    thumb_little.write(receivedData[2]);
    index_finger.write(receivedData[3]);
    middle_finger.write(receivedData[4]);
    ring_pinky.write(receivedData[5]);
    forearm.write(receivedData[6]);
  }
} 
  