
#
from D7Segment import D7Display
import time

print("run...")

display = D7Display(clock_pin=18, data_pin=5)
#display.set_data(1)
#display.set_data(0)
#display.write_byte(111)
#display.write_byte(0)

display.set_brightness(0) 

for i in range(0,999):
  display.set_integer(i)
  time.sleep(.2)

for i in range(0,22):
  print(i)
#  display.set_brightness(i%7)
#  time.sleep(.5)
#  display.set_level(i)
  display.set_digit(0,i)
  display.set_digit(1,i)
  display.set_digit(2,i)
  time.sleep(.5)
#  display.clear_display()
#  time.sleep(1)



