#include <Servo.h>

int x; 
Servo thumb_big;
Servo thumb_little;
Servo index_finger;
Servo middle_finger;
Servo ring_pinky;
Servo forearm;
int receivedData[6];
int i = 0;
bool done = false;

void setup() { 
	Serial.begin(38400); 
  thumb_big.attach(9);
  thumb_little.attach(11);
  index_finger.attach(6);
  middle_finger.attach(10);
  ring_pinky.attach(5);
  forearm.attach(3);

  thumb_big.write(0);
  thumb_little.write(0);
  index_finger.write(0);
  middle_finger.write(0);
  ring_pinky.write(0);
  forearm.write(0);

  pinMode(13, OUTPUT);

  for(int a = 0; a<=5; a++){
    receivedData[a] = 1;
  }

} 
void loop() { 
	if (!Serial.available()){
    digitalWrite(13, LOW);
    if(done==false){
      thumb_big.write(receivedData[0]);
      thumb_little.write(receivedData[1]);
      index_finger.write(receivedData[2]);
      middle_finger.write(receivedData[3]);
      ring_pinky.write(receivedData[4]);
      forearm.write(receivedData[5]);
      // For debug
      /*Serial.print(receivedData[0]);
      Serial.print("-");
      Serial.print(receivedData[1]);
      Serial.print("-");
      Serial.print(receivedData[2]);
      Serial.print("-");
      Serial.print(receivedData[3]);
      Serial.print("-");
      Serial.print(receivedData[4]);
      Serial.print("-");
      Serial.print(receivedData[5]);
      Serial.println();*/
      done = true;
    }
  }

  if(Serial.available()){
    digitalWrite(13, HIGH);
    done = false;
    for(int a=0; a<6; a++){
      receivedData[a] = Serial.read(); 
      delay(10); //necessario
    }
  } 

} 
