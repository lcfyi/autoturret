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
  int isY = Wire.read(); 
  for(int i = 0; i < payload - 1; i++) {
    if(isY) {
      y *= 10;
      y += (int(Wire.read()) - 48);
    } else {
      x *= 10;
      x += (int(Wire.read()) - 48);
    }
  }
  // XXX: do something with these (avg'd) x and y coords
}
