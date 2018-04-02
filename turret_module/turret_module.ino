#include <Wire.h>
#include <Servo.h>

int x = 0;
int transX = 0;
int y = 0;
int transY = 0;
int panPin = 9;
int tiltPin = 10;
Servo pan;
Servo tilt;

int num = 0;
int threat = 0;

void setup() {
  Wire.begin(8); // assign address of 8 to this arduino
  Wire.onReceive(receiveCoords);
  pan.attach(panPin);
  tilt.attach(tiltPin);
}

void loop() {
}

// onReceive event that fires when data from the Pi gets sent over
void receiveCoords(int payload) {
  if(payload > 1) {
    x = 0;
    y = 0;
    num = Wire.read();
    threat = Wire.read();
    for(int i = 0; i < payload - 2; i++) {
      if(num == 0) {
        x *= 10;
        x += (int(Wire.read()) - 48);
      } else if(num == 1) {
        y *= 10;
        y += (int(Wire.read()) - 48);
      } else if(num == 2) {
        continue;
      }
    }
  }
  if(num == 0) {
    transX = map(x, 1, 320, 105, 25);
    pan.write(transX);
  }
  if(num == 1) {
    transY = map(y, 1, 240, 110, 55);
    tilt.write(transY);
  }
}
