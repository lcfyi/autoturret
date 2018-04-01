#include "Keypad.h"
#include <stdlib.h>
#include <serLCD.h>
#include <SoftwareSerial.h>

// -----------------------------------------------------------------------
// modify globals to tailor to different and setups
// -----------------------------------------------------------------------

// KEYPAD: these go in order as listed from 8 --> 1
const int R0 = A0;
const int R1 = A1; 
const int R2 = A2;
const int R3 = A3;
const int C0 = A4; 
const int C1 = A5;
const int C2 = 2;
const int C3 = 3;
const byte ROWS = 4;
const byte COLS = 4;

// PASSWORD (max attempts: 9)
const int NUM_ATTEMPTS = 5;
const int NUM_PASSWORDS = 5;
String database[NUM_PASSWORDS] = {"1234", "6969", "420", "3258", "9993"};
const String OVERRIDE_CODE = "0000";

// LCD
const int LCDPin = 7;

// -----------------------------------------------------------------------

// keymap and keypad rows
char keymap[ROWS][COLS] =
{
{'1', '2', '3', 'A'},
{'4', '5', '6', 'B'},
{'7', '8', '9', 'C'},
{'*', '0', '#', 'D'}
};
byte rPins[ROWS]= {R0, R1, R2, R3};
byte cPins[COLS]= {C0, C1, C2, C3};
Keypad kpd = Keypad(makeKeymap(keymap), rPins, cPins, ROWS, COLS);

int state = 0;
int lastState = state;
int numAttempts = NUM_ATTEMPTS;

// LCD setup 
serLCD lcd(LCDPin);

void sendState(int state);
void updateLCD(int state = -1);
int checkPassword();

String password = "";
char lastKey = NO_KEY;

void setup()
{
  Serial.begin(9600);
  updateLCD(0);
}

void loop()
{
  lastKey = kpd.getKey();
  if(lastKey != NO_KEY)
  {
    if(state == 0) updateLCD();
    if(lastKey == '#')
    {
      switch(checkPassword())
      {
        case 0:
          state = 0;
          updateLCD(state);
          sendState(state);
          lastState = state;
          break;
        case 1:
          state = 1;
          updateLCD(state);
          sendState(state);
          lastState = state;
          break;
        case 2:
          state = 2;
          updateLCD(state);
          sendState(state);
          lastState = state;
          break;
      }
    } else password += lastKey;
  }
}

void sendState(int s)
{
  if(s != lastState)
  {
    switch(s)
    {
      // MODE 0 THREAT 0
      case 0:
        Serial.println("00");
        return;
      // MODE 0 THREAT 1
      case 1:
        Serial.println("01");
        return;
      // MODE 1 THREAT 0 (threat doesn't matter when turret is disabled)
      case 2:
        Serial.println("10");
        return;
    }
  }
}

void updateLCD(int s = -1)
{
  switch(s)
  {
    case 0:
      lcd.clear();
      lcd.print("ARMED -- TRIES:" + String(numAttempts));
      lcd.print("Code: ");
      return;
    case 1: 
      lcd.clear();
      lcd.print("ATTEMPTS REACHED");
      lcd.print("LOCKDOWN MODE ON");
      return;
    case 2:
      lcd.clear();
      lcd.print("DISARMED -- arm ");
      lcd.print("system with 0000");
      return;
    default:
      lcd.print(lastKey);
      return;
  }
}

// only called when # is pressed 
int checkPassword() {
  if(state == 0) 
  {
    numAttempts -= 1;
    for(int i = 0; i < NUM_PASSWORDS; i++) 
    {
      if(database[i] == password)
      {
        password = "";
        numAttempts = NUM_ATTEMPTS;
        return 2;
      }
    }
    if(numAttempts == 0)
    {
      password = "";
      return 1;
    }
    password = "";
    return state;
  }
  else if(state == 1)
  {
    if(password == OVERRIDE_CODE) 
    {
      password = "";
      numAttempts = NUM_ATTEMPTS;
      return 0;
    }
    password = "";
    return state;
  }
  else if(state == 2)
  {
    if(password == OVERRIDE_CODE)
    {
      password = "";
      numAttempts = NUM_ATTEMPTS;
      return 0;
    }
    password = "";
    return state;
  }
}