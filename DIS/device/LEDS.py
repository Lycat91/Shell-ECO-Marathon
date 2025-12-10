import machine, neopixel, utime

NUM_PIXELS = 14
np = neopixel.NeoPixel(machine.Pin(16), NUM_PIXELS)

loop_r = loop_g = loop_b = False
r = b = g = 0

# This delay controls the fade speed. 10ms = 100 steps/sec.
FADE_DELAY_US = 10

while True:
    # Set the color for all pixels in the buffer
    np.fill((r, g, b))
    # Write the data to the LEDs once
    np.write()

    # Update the red color value for the next frame
    if not loop_r:
        r += 1
        if r >= 255: r = 255; loop_r = True
    else:
        r -= 1
        if r <= 0: r = 0; loop_r = False

    utime.sleep_us(FADE_DELAY_US)