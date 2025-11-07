from machine import Pin, UART
import time
import math
import sys
import urandom

### SPI Setup between DIS and OLED ###
DC = 8          # Data/Command
RST = 12        # Reset
MOSI = 11       # Master Out Slave In
SCK = 10        # Serial Clock
CS = 9          # Chip Select (low for communication)

### Pushbutton Setup ###
KEY0 = Pin(15, Pin.IN, Pin.PULL_UP)     # Active Low
KEY1 = Pin(17, Pin.IN, Pin.PULL_UP)     # Active Low

# UART Setup Transmitter
uart = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))

# Modeled Values
voltage = 48.0
current = 0.0
rpm = 0
duty = 0           # 0..100
throttle = 0       # 0..255

# -------- Generator state --------
t0 = time.ticks_ms()
running = True

def format_line(V, I, RPM, DUTY, THROTTLE):
    # Keep floats compact; receiver strips and parses
    return "V={:.2f}, I={:.2f}, RPM={}, DUTY={}, THROTTLE={}\n".format(
        V, I, int(RPM), int(DUTY), int(THROTTLE)
    )

def model_values(t):
    """
    Make values change over time in a believable way.
    t in seconds.
    """
    # Voltage: small ripple around 48 V
    V = 48.0 + 0.2 * math.sin(2*math.pi * 0.3 * t)

    # Throttle ramps 0..255 sawtooth (~6 s period)
    thr = int(( (t % 6.0) / 6.0 ) * 255)

    # Duty mostly tracks throttle but with a smoothing and a cap at 100
    DUTY = min(100, int(thr * 100 / 255))

    # RPM tracks duty with a soft sine variation and a max around ~600 RPM
    RPM = int(DUTY * 6 + 20 * math.sin(2*math.pi * 0.15 * t))
    if RPM < 0:
        RPM = 0

    # Current roughly proportional to duty and rpm (toy model)
    # Add a tiny random dither to look "live"
    I = max(0.0, 0.2 + DUTY * 0.05 + RPM * 0.002 + (urandom.getrandbits(8) - 128)/2048.0)

    return V, I, RPM, DUTY, thr

uart.write("test")