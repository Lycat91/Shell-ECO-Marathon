from machine import Pin, UART
import time
import math
import sys
import urandom


# UART Setup
uart = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))

# Initial Values
voltage = 48.0
current = 0.0
rpm = 0
duty = 0 
throttle = 0

# Generator State
t0 = time.ticks_ms()
running = True


# Format the messages
def format_line(V, I, RPM, DUTY, THROTTLE):
    # Keep floats compact; receiver strips and parses
    return "V={:.2f}, I={:.2f}, RPM={}, DUTY={}, THROTTLE={}\n".format(
        V, I, int(RPM), int(DUTY), int(THROTTLE)
    )

def send_one_sample(force=False):
    global voltage, current, rpm, duty, throttle

    # Update model if running or if forced (burst)
    now_ms = time.ticks_ms()
    t = time.ticks_diff(now_ms, t0) / 1000.0
    if running or force:
        voltage, current, rpm, duty, throttle = model_values(t)

    line = format_line(voltage, current, rpm, duty, throttle)
    print(line)
    try:
        uart.write(line)
    except Exception as e:
        # If TX breaks, at least print it to USB REPL for debugging
        sys.print_exception(e)
        print(line, end="")


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

### Main Program ###
print("Starting simulation")
period_ms = 250
next_ms = time.ticks_add(time.ticks_ms(), period_ms)

while True:
    now = time.ticks_ms()
    if time.ticks_diff(now, next_ms) >= 0:
        next_ms = time.ticks_add(now, period_ms)

        send_one_sample()


