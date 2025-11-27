#include <SPI.h>
#include <Ethernet.h>
#include <Servo.h> 
#include "Mudbus.h"

Mudbus Mb;

int pwm_a = 6;
int dir_a = 7;
int dir_a2 = 5;

int buzzer = 3;
// int pwm_b = 9;
// int dir_b = 12;

int gaugePin=8;
int first_run=true;
int speed_;
int gaugeVal;
Servo gauge; 
int max_speed=15000;
int min_speed=5000;
int default_speed=8000;



// Buzzer alarm variables
unsigned long previousMillis = 0; 
const long interval = 500; // Interval at which to beep (milliseconds)

void setup() {
   
  Serial.begin(9600);
  uint8_t mac[]     = { 0xA8, 0x61, 0x0A, 0xAE, 0xE2, 0x09 };//C8-4B-D6-4A-83-68
  uint8_t ip[]      = { 192,168, 1, 177};
  uint8_t gateway[] = { 192,168, 1, 1};
  uint8_t subnet[]  = { 255, 255, 255, 0 };
  Ethernet.begin(mac, ip, gateway, subnet);

  pinMode(pwm_a, OUTPUT);
  pinMode(dir_a, OUTPUT);
  digitalWrite(dir_a, HIGH); 
  pinMode(dir_a2, OUTPUT);
  digitalWrite(dir_a2, LOW); 

  //smoke generator
  // pinMode(pwm_b, OUTPUT);
  // pinMode(dir_b, OUTPUT);
  // digitalWrite(dir_b, LOW); 
  // analogWrite(pwm_b, 0);
  
  // buzzer 
  pinMode(buzzer , OUTPUT);
  
  gauge.attach(gaugePin); 
}

void loop(){
  Mb.Run(); 

  //First execution default values
  if (first_run == true)
  {
    Mb.R[6]=default_speed;
    Mb.R[7]=0;
    first_run=false;
  }

  //min & max value
  if(Mb.R[6]>max_speed)
    Mb.R[6]=max_speed;
  if(Mb.R[6]<min_speed)
    Mb.R[6]=min_speed;

  Serial.print("Mb.R[6]: ");
  Serial.println(Mb.R[6]);
  Serial.print("Mb.R[7]: ");
  Serial.println(Mb.R[7]);

  speed_=map(Mb.R[6], min_speed, max_speed, 35, 150);
  Serial.print("Speed: ");
  Serial.println(speed_);
  
  gaugeVal=map(speed_, 35, 150, 0, 250);
  Mb.R[7]=gaugeVal;
  Serial.print("Gauge: ");
  Serial.print(gaugeVal);
  Serial.println(" degrees");

  // Buzzer alarm control
  unsigned long currentMillis = millis();
  if (gaugeVal ==35) {
    if (currentMillis - previousMillis >= interval) {
      previousMillis = currentMillis; 
      if (digitalRead(buzzer) == LOW) {
        digitalWrite(buzzer, HIGH); // Turn buzzer on
      } else {
        digitalWrite(buzzer, LOW); // Turn buzzer off
      }
    }
  } else if(gaugeVal ==110){
    while(true){
      digitalWrite(buzzer, HIGH); // Keep buzzer on if gauge value is high
      delay(2000); // Buzzer will beep every second
      digitalWrite(buzzer, LOW);
      delay(1000);
    }
  }else {
    digitalWrite(buzzer, LOW); // Keep buzzer off if gauge value is low
  }
  
  //set value for real
  analogWrite(pwm_a, speed_);
  gauge.write(180-gaugeVal);

  delay(100); 
   
}
