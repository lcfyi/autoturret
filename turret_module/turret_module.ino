#include <Wire.h>

int x = 0; 
int y = 0; 

void setup() {
  Wire.begin(8); // assign address of 8 to this arduino
  Wire.onReceive(receiveCoords);
  Serial.begin(9600);
}

void loop() {
}

// onReceive event that fires when data from the Pi gets sent over
void receiveCoords(int payload) {
  if(payload > 1) {
    int isY = Wire.read(); 
    int threat = Wire.read();
    for(int i = 0; i < payload - 2; i++) {
      if(isY) {
        y *= 10;
        y += (int(Wire.read()) - 48);
      } else {
        x *= 10;
        x += (int(Wire.read()) - 48);
      }
    }
  }
  if(isY) {
    Serial.print("Y: ");
    Serial.println(y);
  } else {
    Serial.print("X: ");
    Serial.println(x);
  }
  x = 0;
  y = 0;
  // XXX: do something with these (avg'd) x and y coords
}
