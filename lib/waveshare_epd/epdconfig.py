import os
import logging
import sys
import time
import spidev
import RPi.GPIO as GPIO

# Pin definition
RST_PIN         = 17
DC_PIN          = 25
CS_PIN          = 8
BUSY_PIN        = 24

# Display resolution
EPD_WIDTH       = 800
EPD_HEIGHT      = 480

class RaspberryPi:
    def __init__(self):
        self.GPIO = GPIO
        self.SPI = spidev.SpiDev()

    def digital_write(self, pin, value):
        self.GPIO.output(pin, value)

    def digital_read(self, pin):
        return self.GPIO.input(pin)

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.SPI.writebytes(data)

    def spi_writebyte2(self, data):
        self.SPI.writebytes2(data)

    def module_init(self):
        self.GPIO.setmode(self.GPIO.BCM)
        self.GPIO.setwarnings(False)
        self.GPIO.setup(RST_PIN, self.GPIO.OUT)
        self.GPIO.setup(DC_PIN, self.GPIO.OUT)
        self.GPIO.setup(CS_PIN, self.GPIO.OUT)
        self.GPIO.setup(BUSY_PIN, self.GPIO.IN)

        # Initialize SPI
        self.SPI.open(0, 0)  # Open SPI port 0, device (CS) 0
        self.SPI.max_speed_hz = 4000000
        self.SPI.mode = 0b00
        return 0

    def module_exit(self):
        logging.debug("spi end")
        self.SPI.close()

        logging.debug("close 5V, Module enters 0 power consumption ...")
        self.GPIO.output(RST_PIN, 0)
        self.GPIO.output(DC_PIN, 0)

        self.GPIO.cleanup([RST_PIN, DC_PIN, CS_PIN, BUSY_PIN])

# Export the GPIO pins and SPI device
RST_PIN = RST_PIN
DC_PIN = DC_PIN
CS_PIN = CS_PIN
BUSY_PIN = BUSY_PIN

implementation = RaspberryPi()

### Basic interface
def module_init():
    return implementation.module_init()

def module_exit():
    implementation.module_exit()

def digital_write(pin, value):
    implementation.digital_write(pin, value)

def digital_read(pin):
    return implementation.digital_read(pin)

def delay_ms(delaytime):
    implementation.delay_ms(delaytime)

def spi_writebyte(data):
    implementation.spi_writebyte(data)

def spi_writebyte2(data):
    implementation.spi_writebyte2(data)