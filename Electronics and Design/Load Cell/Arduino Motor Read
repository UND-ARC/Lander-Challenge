#include <Arduino.h>
#include "HX711.h"
#include <Servo.h>

Servo ESC;
Servo ESC1;
int angle = 0;
int angle2 = 180;
int angle3 = 0;

// HX711 circuit wiring
float read;
const int LOADCELL_DOUT_PIN = 2;
const int LOADCELL_SCK_PIN = 3;
float timer = 0;

HX711 scale;

void setup() {
  ESC.attach(9, 1000, 2000);
  ESC1.attach(10, 1000, 2000);

  Serial.begin(9600);

  ESC.write(angle3);
  ESC1.write(angle3);
  delay(10000);
 
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(110700/282);                      // this value is obtained by calibrating the scale with known weights; see the README for details
  scale.tare();  
}

void loop() {
  if (angle <= 180)
  {
    timer = millis();
    Serial.print("Time: ");
    Serial.print(timer/1000, 3);
    if (timer < 10000)
    {
      Serial.print(" ");
    }
    Serial.print(" \t");
    Serial.print("Weight: ");
    ESC.write(angle);
    ESC1.write(angle);
    read = scale.get_units();
    Serial.print(read);
    Serial.print("                            ");
    Serial.print("Angle: ");
    Serial.println(angle);
    angle++;
    //delay(1000);
  }
  
  else if (angle2 >= 0)
  {
    timer = millis();
    Serial.print("Time: ");
    Serial.print(timer/1000, 3);
    if (timer < 10000)
    {
      Serial.print(" ");
    }
    Serial.print(" \t");
    Serial.print("Weight: ");
    ESC.write(angle2);
    ESC1.write(angle2);
    read = scale.get_units();
    Serial.print(read);
    Serial.print("                            ");
    Serial.print("Angle: ");
    Serial.println(angle2);
    angle2--;
  }
  else
  {
    ESC.write(angle3);
    ESC.write(angle3);
    return;
  }
  
}