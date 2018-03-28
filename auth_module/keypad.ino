#include "Keypad.h"
#include <stdlib.h>

const byte Rows = 4; //number of rows on the keypad i.e. 4
const byte Cols = 4; //number of columns on the keypad i,e, 3

int numAttempts = 0;

int timer = millis(); // Amount of time given to user to enter a code before being stuck in an override state

const String OVERRIDE= "0000";
const int numOfPasswords = 5; // How many passwords that can be stored in our databasae
String database[numOfPasswords]= { "1234", "6969", "420", "Test", "Test123" };

//we will define the key map as on the key pad:

char keymap[Rows][Cols]=      
{
{'1', '2', '3', 'A'},   
{'4', '5', '6', 'B'},
{'7', '8', '9', 'C'},
{'*', '0', '#', 'D'}
};

//  a char array is defined as it can be seen on the above


//keypad connections to the arduino terminals is given as:

byte rPins[Rows]= {A0,A1,A2,A3}; //Rows 0 to 3    
byte cPins[Cols]= {A4,A5,A6,A7}; //Columns 0 to 2

// command for library forkeypad
//initializes an instance of the Keypad class
Keypad kpd= Keypad(makeKeymap(keymap), rPins, cPins, Rows, Cols);
//If key is not equal to 'NO_KEY', then this key is printed out

void setup()
{
  Serial.begin(9600);
}


void loop() 
{
  char keypressed = kpd.getKey();
  if (keypressed != NO_KEY)        // When a key is pressed it'll run the following code.
  {
    String password = readKey(keypressed);    // Will read the inputs given in the keypad if false increments by 1
   
    if(checkPassword(password))
    {  
      return 1;
    }

    numAttempts++;

    if (numAttempts > 5)
    {
      overrideState(keypressed);    // If given more than 5 attempts you must enter the override code to reset the system
    }
  }
}

String readKey(char keypressed)
{
  bool enter = true;
  String password;
  while(enter)
  {
    elapsed = millis()-timer;
    if(elapsed>30000)
    {
      return "666";
    }  // Essentially we implemented a timer in which failing to enter a code in a specifc time will increment the number of attempts
    
    char key = kpd.waitForKey();//kpd.getKey();
          
    switch(key)
    {
      case 'A': enter = false; break;  // Enter once done inputting codes
      case 'C': password = ""; break;  // Clears input
      default:
      Serial.println(key);
      password += key;   // Reads input and adds it to password
    }

  }

  return password;
}

bool checkPassword(String password)
{
  if (password == "666")
  {
    return false;
  }
  for (int j=0; j < numOfPasswords ; j++)
  {
    if( database[j] == password ) // Checks entire database to see if there's a match in the inputted code
    {
      return true; 
    }
      return false;
  }
}
  
int overrideState(char keypressed)
{
  while(readKey(keypressed)!=OVERRIDE)
  {
  }
  numAttempts = 0;
}                 


  
