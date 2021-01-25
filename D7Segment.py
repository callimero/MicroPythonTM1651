"""Micropython Library for the 3 7-seqment LED display (aka "Gotek" Display) using the TM1651 chip.

Based and adapted from Koen Vervloesem Raspberry Pi Version
Copyright (C) 2020 Koen Vervloesem (battery graph versrion)
Copyright (C) 2021 Carsten Wartmann Changes for LED 7-segments, Micropyhton version

SPDX-License-Identifier: MIT
Based on:
https://github.com/koenvervloesem/rpi-mini-battery-display/blob/master/rpi_mini_battery_display/__main__.py
https://github.com/coopzone-dc/GotekLEDC68
"""

from time import sleep
from machine import Pin

# 0 1 2 3 4 5 6 7 8 9
# A B C D E F
#   o   _    _
#     o   _ -=
CHAR_ARRAY = [
  0x3f, 0x06, 0x5b, 0x4f, 0x66, 0x6d, 0x7d, 0x07, 0x7f, 0x6f,
  0x77, 0x7c, 0x39, 0x5e, 0x79, 0x71,
  0x00, 0x63, 0x5c, 0x01, 0x40, 0x08, 0x49
] 

# The TM1651's maximum frequency is 500 kHz with a 50% duty cycle.
# We take a conservative clock cycle here.
TM1651_CYCLE = 0.000050  # 50 microseconds


class Command():
     # Data commands fro the chip
    ADDR_FIXED = 0x44  # Set fixed address mode
    # Display control commands
    DISPLAY_OFF = 0x80  # Set display off
    DISPLAY_ON = 0x88  # Set display on
    # Address commands
    ADDR_START = 0xC0  # Set address of the display register



class D7Display:
    """Class to control the TM1651 3x8 segments display.
    The TM1651 chip communicates using a two-line serial bus interface.
    """

    def __init__(self, clock_pin=18, data_pin=5):
        """Initialize the TM1651 display object."""
        self.clock_pin = Pin(clock_pin, Pin.OUT)
        self.data_pin = Pin(data_pin, Pin.OUT)
        
        print("Pins set!")

        self.set_brightness(2)
        ack = self.clear_display()
#        print("ACK: ",ack)

        # If the TM1651 hasn't returned an ACK,
        # assume that no LED controller is connected on these pins.
        if not ack:
            sys.exit(retval=0)
        
        
    def set_brightness(self, brightness):
        self.brightness = brightness
    
    def clear_display(self):
        self.set_digit(0,16)
        self.set_digit(1,16)
        self.set_digit(1,16)
        
        
    def set_integer(self, num):
      if num>999:
        num=999
      self.set_digit(0,int(num/100)%10)
      self.set_digit(1,int(num/10)%10)
      self.set_digit(2,int(num/1)%10)
      
      
    def set_digit(self, digit, num):
        ack = True
        ack = self.send_command(Command.ADDR_FIXED) and ack
        ack = self.send_command(Command.ADDR_START+digit, CHAR_ARRAY[num]) and ack
        ack = self.send_command(Command.DISPLAY_ON + self.brightness) and ack
        return ack
        
    def send_command(self, *data):
        ack = True
        self.start()
        for byte in data:
            ack = self.write_byte(byte) and ack
        self.stop()
        return ack


    def delineate_transmission(self, begin):
        # DIO changes its value while CLK is HIGH.
        self.set_data(begin)
        sleep(TM1651_CYCLE / 2)

        self.set_clock(1)
        sleep(TM1651_CYCLE / 4)

        self.set_data(not begin)
        sleep(TM1651_CYCLE / 4)

    def start(self):
        """Start a data transmission to the TM1651."""
        # DIO changes from HIGH to low while CLK is high.
        # CLK ____████
        # DIO ██████__
        self.delineate_transmission(1)

    def stop(self):
        """Stop a data transmission to the TM1651."""
        # DIO changes from LOW to HIGH while CLK is HIGH.
        # CLK ____████
        # DIO ______██
        self.delineate_transmission(0)
    
    def set_clock(self, state):
        #GPIO.output(self.clock_pin, state)
        self.clock_pin.value(state)

    def set_data(self, state):
        """Set the state of the data pin: HIGH or LOW."""
        #GPIO.output(self.data_pin, state)
        self.data_pin.value(state)
    
    def half_cycle_clock_low(self, write_data):
        """Start the first half cycle when the clock is low and write a data bit."""
        self.set_clock(0)
        sleep(TM1651_CYCLE / 4)

        self.set_data(write_data)
        sleep(TM1651_CYCLE / 4)
        
    def half_cycle_clock_high(self):
        self.set_clock(1)
        sleep(TM1651_CYCLE / 2)

    def half_cycle_clock_high_ack(self):
        # Set CLK high.
        self.set_clock(1)
        sleep(TM1651_CYCLE / 4)

        # Set DIO to input mode and check the ack.
        #GPIO.setup(self.data_pin, IN)
        self.data_pin(Pin.IN)
        #ack = GPIO.input(self.data_pin)
        ack = self.data_pin.value()
        
        # ack (DIO) should be LOW now
        # Now we have to set it to LOW ourselves before the TM1651
        # releases the port line at the next clock cycle.
        #GPIO.setup(self.data_pin, OUT)
        self.data_pin(Pin.OUT)
        if not ack:
            self.set_data(0)

        sleep(TM1651_CYCLE / 4)
        # Set CLK to low again so it can begin the next cycle.
        self.set_clock(0)

        return ack
    
    def write_byte(self, write_data):
        #print("write: ",write_data)
        # Send 8 data bits, LSB first.
        # A data bit can only be written to DIO when CLK is LOW.
        # E.g. write 1 to DIO:
        # CLK ____鈻堚枅鈻堚枅
        # DIO __鈻堚枅鈻堚枅鈻堚枅
        for _ in range(8):
            self.half_cycle_clock_low(write_data & 0x01)
            self.half_cycle_clock_high()

            # Take the next bit.
            write_data >>= 1

        # After writing 8 bits, start a 9th clock ycle.
        # During the 9th half-cycle of CLK when it is LOW,
        # if we set DIO to HIGH the TM1651 gives an ack by
        # pulling DIO LOW:
        # CLK ____鈻堚枅鈻堚枅
        # DIO __鈻坃____
        # Set CLK low, DIO high.
        self.half_cycle_clock_low(1)
        # Return True if the ACK was LOW.
        return not self.half_cycle_clock_high_ack()
       
    #class GeneralError(Exception):
    #  print("OHoho!!!!!!!!!!!!!!!!!!!!!!! ",Exception)





