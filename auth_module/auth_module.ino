#include "Keypad.h"
#include <stdlib.h>
#include <serLCD.h>
#include <SoftwareSerial.h>

const byte Rows= 4; //number of rows on the keypad i.e. 4
const byte Cols= 4; //number of columns on the keypad i,e, 3

int numAttempts = 5;
char state = '1'; // 0 is unarmed 1 is armed.
char laser = '0';

String stateToPi;

int timer = millis(); // Amount of time given to user to enter a code before being stuck in an override state

const String OVERRIDE= "0000";
const int numOfPasswords = 5; // How many passwords that can be stored in our databasae
String database[numOfPasswords]= { "1234", "6969", "420", "Test", "Test123" };


const int LCDPin = 7;

serLCD lcd(LCDPin);
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
// for mega
//byte rPins[Rows]= {A0,A1,A2,A3}; //Rows 0 to 3    
//byte cPins[Cols]= {A4,A5,A6,A7}; //Columns 0 to 2

// for uno
byte rPins[Rows] = {A0, A1, A2, A3};
byte cPins[Cols] = {A4, A5, 2, 3};



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

     currentState(state);
     lcd.clear();
     
     char keypressed = kpd.getKey();
   
     if (keypressed != NO_KEY)        // When a key is pressed it'll run the following code.
     { 
       
       String password= readKey(keypressed);    // Will read the inputs given in the keypad if false increments by 1
       if(checkPassword(password))
       {
        LCDDisp(1);
        state = '0';
        laser = '0';
        return finalState();
       
        
       }

       if (state == '0' && laser == '1')
       {
          lcd.clear();
       }
      else{ 
      --numAttempts;
       LCDDisp(3);
       laser = '1';
       state ='1';
      }
       
       
       if (numAttempts <= 0)
       {
         LCDDisp(2);
         laser = '1';
        return finalState();
         
       }
      
     }

}




String readKey(char keypressed)
{
     if (state == '0' && laser == '0')
     {
        turnOff(); 
     }

     currentState(state);

     if (state == '0' && laser == '1')
     {
        lcd.clear(); 
        lcd.print("Disarmed:");      
     }
     
     lcd.setCursor(2,1);
      bool enter = true;
      String password;
      int pressed = 0;
      char key = keypressed;
        while(enter)
        {
         
         if (pressed > 0)
         {
         int elapsed = millis()-timer;
         // if(elapsed>3000){return "666";}  // Essentially we implemented a timer in which failing to enter a code in a specifc time will increment the number of attempts
            
            key = kpd.waitForKey();//kpd.getKey();
            if (pressed > 15)
              {
                key = '#';
              }
          
         }

         switch(key)
            {
               case '#': enter = false; break;  // Enter once done inputting codes
               case '*': password = ""; lcd.clear(); currentState(state); lcd.setCursor(2,1); pressed=0; key = kpd.waitForKey(); break;  // Clears input
               default:
               pressed++;
               LCDPressed(key);
               password += key;   // Reads input and adds it to password
            }

        }
        if (state == '0' && laser == '1')
        {
          laser = '0';
          return password;
        }
        return password;
}




bool checkPassword(String password)
{
 if (password == "666"){return false;}
 if (password == OVERRIDE){state = '0'; laser = '1'; numAttempts = 5; return false;}
  for (int j=0; j < numOfPasswords ; j++)
  {
    if( database[j] == password ) // Checks entire database to see if there's a match in the inputted code
    {
      return true; 
    }
      return false;
  } 
}
  

void LCDPressed(char key)
{
lcd.print(String(key));
}


void LCDDisp(int disp)
{
  lcd.clear();
  switch(disp)
  {
    case 1: lcd.print("Correct code"); delay(2000); break;
    case 2:  lcd.print("Armed:");lcd.setCursor(2,1);lcd.print("Terminating"); delay(1000); break;
    case 3: lcd.print("Incorrect code"); lcd.setCursor(2,1); lcd.print("Attempts left: "); lcd.print(String(numAttempts));  delay(1); break;
  }  
}



void currentState(char code)
{
  switch(code)
  {
    case '0': lcd.print("Disarmed:"); if (laser=='1'){lcd.setCursor(2,1); lcd.print("Override State");} break;
    case '1': lcd.print("Armed:"); break;
  }

}

void turnOff()
{
 lcd.print("Disarmed:");
 while(true)
 {
  true;
 }
}

String finalState()
{
  stateToPi+=state;
  stateToPi+=laser;
  return stateToPi;  
}



  

