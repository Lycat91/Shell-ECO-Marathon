from machine import Pin, SPI
import framebuf
import time

# ---------------------- OLED Pin Configuration ----------------------
DC = 8       # Data/Command control pin
RST = 12     # Reset pin
MOSI = 11    # SPI data pin
SCK = 10     # SPI clock pin
CS = 9       # Chip select pin

# ---------------------- OLED Driver Class ----------------------
class OLED_1inch3(framebuf.FrameBuffer):
    def __init__(self):
        # Screen dimensions
        self.width = 128
        self.height = 64

        self.rotate = 180  # Rotation: 0 or 180 degrees (changes orientation)

        # Initialize pins
        self.cs = Pin(CS, Pin.OUT)
        self.rst = Pin(RST, Pin.OUT)
        self.dc = Pin(DC, Pin.OUT)
        self.cs(1)

        # Initialize SPI bus
        self.spi = SPI(1, baudrate=20000000, polarity=0, phase=0, sck=Pin(SCK), mosi=Pin(MOSI))

        # Create framebuffer (pixel buffer in memory)
        self.buffer = bytearray(self.width * self.height // 8)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_HMSB)

        # Define "colors" for drawing
        self.white = 0xFFFF   # Pixel on
        self.black = 0x0000   # Pixel off

        # Initialize OLED hardware
        self.init_display()

    # ------------------ Low-level command/data functions ------------------
    def write_cmd(self, cmd):
        """Send a single command byte to the OLED"""
        self.cs(1)
        self.dc(0)   # Command mode
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        """Send a single data byte to OLED"""
        self.cs(1)
        self.dc(1)   # Data mode
        self.cs(0)
        self.spi.write(bytearray([buf]))
        self.cs(1)

    # ------------------ Initialize OLED ------------------
    def init_display(self):
        """Send commands to setup SH1107 display"""
        self.rst(1)
        time.sleep(0.001)
        self.rst(0)
        time.sleep(0.01)
        self.rst(1)

        self.write_cmd(0xAE)  # Turn display OFF
        self.write_cmd(0x00)  # Lower column start address
        self.write_cmd(0x10)  # Higher column start address
        self.write_cmd(0xB0)  # Page start address
        self.write_cmd(0xDC)  # Display start line command
        self.write_cmd(0x00)  # Offset
        self.write_cmd(0x81)  # Set contrast
        self.write_cmd(0xAF)  # Contrast value (0–255)
        self.write_cmd(0x21)  # Set memory addressing mode
        if self.rotate == 0:
            self.write_cmd(0xA0)  # Segment remap
        else:
            self.write_cmd(0xA1)
        self.write_cmd(0xC0)  # COM scan direction
        self.write_cmd(0xA4)  # Disable Entire Display On
        self.write_cmd(0xA6)  # Normal display (A7 = inverted)
        self.write_cmd(0xA8)  # Multiplex ratio
        self.write_cmd(0x3F)  # 1/64 duty
        self.write_cmd(0xD3)  # Set display offset
        self.write_cmd(0x60)  # Offset value
        self.write_cmd(0xD5)  # Set display clock
        self.write_cmd(0x41)
        self.write_cmd(0xD9)  # Set pre-charge period
        self.write_cmd(0x22)
        self.write_cmd(0xDB)  # Set VCOMH deselect level
        self.write_cmd(0x35)
        self.write_cmd(0xAD)  # Charge pump setting
        self.write_cmd(0x8A)  # Enable DC-DC
        self.write_cmd(0xAF)  # Turn display ON

    # ------------------ Push framebuffer to OLED ------------------
    def show(self):
        """Copy framebuffer memory to OLED"""
        self.write_cmd(0xB0)  # Start page
        for page in range(0, 64):
            if self.rotate == 0:
                self.column = 63 - page
            else:
                self.column = page

            self.write_cmd(0x00 + (self.column & 0x0F))  # Lower column address
            self.write_cmd(0x10 + (self.column >> 4))    # Higher column address
            for num in range(0, 16):
                self.write_data(self.buffer[page * 16 + num])

# ---------------------- Main Program ----------------------
oled = OLED_1inch3()             # Initialize OLED
oled.fill(oled.black)            # Clear screen
oled.show()

# ---------------------- Real-time Seconds Counter ----------------------
start_time = time.ticks_ms()     # Record start time in milliseconds
update_interval = 0.1          # OLED refresh interval in seconds

while True:
    # Calculate elapsed time in seconds (real-life seconds)
    elapsed_ms = time.ticks_diff(time.ticks_ms(), start_time)
    seconds = elapsed_ms / 1000  # Convert ms to seconds

    # ---------------------- Update OLED ----------------------
    oled.fill(oled.black)           # Clear screen
    oled.text("HELLO", 35, 10)     # Static text at top
    oled.text("Seconds:", 10, 30)  # Label for timer
    oled.text("{:.2f}".format(seconds), 80, 30)  # Timer in seconds with 2 decimal places
    oled.show()                     # Push framebuffer to OLED

    # ---------------------- Wait before next update ----------------------
    time.sleep(update_interval)     # Refresh interval
