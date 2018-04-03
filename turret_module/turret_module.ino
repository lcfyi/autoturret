#include <Wire.h>
#include <Servo.h>

// -----------------------------------------------------------------------
// modify globals here to tailor it to different boards
// -----------------------------------------------------------------------

const int PAN_PIN = 9;
const int TILT_PIN = 10;
const int LED_PIN = 6;
const int I2C_ADDRESS = 8;

// -----------------------------------------------------------------------


int x = 0;
int transX = 0;
int y = 0;
int transY = 0;

Servo pan;
Servo tilt;

int num = 0;
int threat = 0;

void setup() 
{
  Wire.begin(I2C_ADDRESS); // assign address of 8 to this arduino
  Wire.onReceive(receiveCoords);
  pan.attach(PAN_PIN);
  tilt.attach(TILT_PIN);
  pinMode(LED_PIN, OUTPUT);
}

void loop() 
{
}

// onReceive event that fires when data from the Pi gets sent over
void receiveCoords(int payload) 
{
  x = 0;
  y = 0;
  num = Wire.read();
  threat = Wire.read();
  for(int i = 0; i < payload - 2; i++) 
  {
    if(num == 0) 
    {
      x *= 10;
      x += (int(Wire.read()) - 48);
    } 
    else if(num == 1) 
    {
      y *= 10;
      y += (int(Wire.read()) - 48);
    }
  }
  if(num == 0)
  {
    pan.attach(PAN_PIN);
    transX = map(x, 1, 320, 105, 25);
    pan.write(transX);
  }
  if(num == 1) 
  {
    tilt.attach(TILT_PIN);
    transY = map(y, 1, 240, 110, 55);
    tilt.write(transY);
  }
  if(threat == 0) 
  {
    digitalWrite(LED_PIN, LOW);
  }
  if(threat == 1) 
  {
    digitalWrite(LED_PIN, HIGH);
  }
  // clear any remaining things in the pipeline
  while(Wire.available()) 
  {
    Wire.read();
  }
}
