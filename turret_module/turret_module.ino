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
  Wire.onReceive(receiveCoords); // event that fires whenever i2c is received
  pan.attach(PAN_PIN); // set up our pan servo
  tilt.attach(TILT_PIN); // set up our tilt servo
  pinMode(LED_PIN, OUTPUT); // set up our LED pin
}

// nothing in our loop because we don't want our code to do anything without an event
void loop() 
{
}

// onReceive event that fires when data from the Pi gets sent over
void receiveCoords(int payload) 
{
  // reset our x and y variables whenever something new comes in the i2c pipeline
  x = 0;
  y = 0;

  // assign the first byte to num (indicates what type of data it is)
  // num 0 is x coordinate, num 1 is y coordinate
  num = Wire.read();

  // assign the second byte to threat (indicates whether laser should be on)
  threat = Wire.read();
  
  // loop through the rest of the received bytes (-2 since we've read two already)
  for(int i = 0; i < payload - 2; i++) 
  {
    // as mentioned before, if num is 0, it's the x coordinate
    if(num == 0) 
    {
      // reconstruct the bytes for each number
      x *= 10;
      x += (int(Wire.read()) - 48);
    }
    // otherwise it's the y coordinate
    else if(num == 1) 
    {
      y *= 10;
      y += (int(Wire.read()) - 48);
    }
  }

  // now that we have our coordinates, we have to update the servo
  // if num is 0, it's the x coordinate
  if(num == 0)
  {
    // translate our coordinate to a servo angle (calibrated)
    transX = map(x, 1, 320, 105, 25);
    // write that angle to our servo
    pan.write(transX);
  }
  // if num is 1, it's the y coordinate
  if(num == 1) 
  {
    // same process as above
    transY = map(y, 1, 240, 110, 55);
    tilt.write(transY);
  }

  // we also have to update our threat if something has changed
  if(threat == 0) 
  {
    // threat is 0, turn LED off
    digitalWrite(LED_PIN, LOW);
  }
  if(threat == 1) 
  {
    // threat is 1, turn LED on 
    digitalWrite(LED_PIN, HIGH);
  }

  // clear any remaining things in the pipeline
  while(Wire.available())
  {
    Wire.read();
  }
}
