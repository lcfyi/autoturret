#include <Wire.h>
#include <Servo.h>

int x = 0;
int transX = 0;
int y = 0;
int transY = 0;
Servo serv;

int num = 0;
int threat = 0;

void setup() {
  Wire.begin(8); // assign address of 8 to this arduino
  Wire.onReceive(receiveCoords);
  Serial.begin(9600);
  serv.attach(9);
}

void loop() {

}

// onReceive event that fires when data from the Pi gets sent over
void receiveCoords(int payload) {
  x = 0;
  y = 0;
  if(payload > 1) {
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
    transX = map(x, 1, 320, 95, 25);
    Serial.println(transX);
    serv.write(transX);
  }
  if(num) {
    Serial.print("Y: ");
    Serial.println(y);
  } else {
    Serial.print("X: ");
    Serial.println(x);
  }
  // XXX: do something with these (avg'd) x and y coords
}
