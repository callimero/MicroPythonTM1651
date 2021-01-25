# With Gotek LED

import dht
import machine
import time
import D7Segment

display = D7Segment.D7Display(clock_pin=18, data_pin=5)
d = dht.DHT22(machine.Pin(4))

def led_temp(temp):
      if temp>999:
        temp=999
      display.set_digit(0,int(temp/10)%10)
      display.set_digit(1,int(temp/1)%10)
      display.set_digit(2,17)
      
def led_humid(humi):
      if humi>999:
        humi=999
      display.set_digit(0,int(humi/10)%10)
      display.set_digit(1,int(humi/1)%10)
      display.set_digit(2,22)
      


while 1:
  d.measure()
  print(d.temperature())
  print(d.humidity())
  led_temp(d.temperature())
  time.sleep(5)
  led_humid(d.humidity())
  
  time.sleep(5)




