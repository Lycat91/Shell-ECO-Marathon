from machine import Pin, SPI, UART
import framebuf, time
import micropython

# ------- Pins -------
DC, RST, MOSI, SCK, CS = 8, 12, 11, 10, 9

# Pushbuttons (unchanged)
KEY0 = Pin(15, Pin.IN, Pin.PULL_UP)
KEY1 = Pin(17, Pin.IN, Pin.PULL_UP)

# UART (unchanged)
uart = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))

# OLED Display Setup
class OLED_1inch3(framebuf.FrameBuffer):
    def __init__(self):
        self.width = 128
        self.height = 64
        self.rotate = 180

        self.cs = Pin(CS, Pin.OUT)
        self.rst = Pin(RST, Pin.OUT)
        self.dc = Pin(DC, Pin.OUT)
        self.cs(1)

        self.spi = SPI(1,30000_000,polarity=0, phase=0,sck=Pin(SCK),mosi=Pin(MOSI),miso=None)
        self.dc = Pin(DC,Pin.OUT)
        self.dc(1)
        self.buffer = bytearray(self.height * self.width // 8)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_HMSB)
        self.init_display()

        # -------- Button state ----------
        now = time.ticks_ms()
        self.key0 = KEY0
        self.key1 = KEY1
        self._debounce_ms = 150
        self._longpress_ms = 3000
        self._reset_alert_ms = 3000
        self._last_key0 = self.key0.value()
        self._last_key1 = self.key1.value()
        self._last_time_k0 = now
        self._last_time_k1 = now
        self._k1_press_start = None
        self._k1_reset_fired = False
        
    def write_cmd(self, cmd):
        self.cs(1); self.dc(0); self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.cs(1); self.dc(1); self.cs(0)
        if isinstance(buf, int):
            self.spi.write(bytes([buf]))
        else:
            self.spi.write(buf)  # send the whole buffer/slice as-is
        self.cs(1)


    def init_display(self):
        self.rst(1)
        time.sleep(0.001)
        self.rst(0)
        time.sleep(0.01)
        self.rst(1)
        
        self.write_cmd(0xAE)#turn off OLED display

        self.write_cmd(0x00)   #set lower column address
        self.write_cmd(0x10)   #set higher column address 

        self.write_cmd(0xB0)   #set page address 
      
        self.write_cmd(0xdc)    #et display start line 
        self.write_cmd(0x00) 
        self.write_cmd(0x81)    #contract control 
        self.write_cmd(0x6f)    #128
        self.write_cmd(0x21)    # Set Memory addressing mode (0x20/0x21) #
        if self.rotate == 0:
            self.write_cmd(0xa0)    #set segment remap
        elif self.rotate == 180:
            self.write_cmd(0xa1)
        self.write_cmd(0xc0)    #Com scan direction
        self.write_cmd(0xa4)   #Disable Entire Display On (0xA4/0xA5) 

        self.write_cmd(0xa6)    #normal / reverse
        self.write_cmd(0xa8)    #multiplex ratio 
        self.write_cmd(0x3f)    #duty = 1/64
  
        self.write_cmd(0xd3)    #set display offset 
        self.write_cmd(0x60)

        self.write_cmd(0xd5)    #set osc division 
        self.write_cmd(0x41)
    
        self.write_cmd(0xd9)    #set pre-charge period
        self.write_cmd(0x22)   

        self.write_cmd(0xdb)    #set vcomh 
        self.write_cmd(0x35)  
    
        self.write_cmd(0xad)    #set charge pump enable 
        self.write_cmd(0x8a)    #Set DC-DC enable (a=0:disable; a=1:enable)
        self.write_cmd(0XAF)

    def show(self):
        self.write_cmd(0xB0)
        for page in range(0, 64):
            column = page if self.rotate == 180 else (63 - page)
            self.write_cmd(0x00 + (column & 0x0F))
            self.write_cmd(0x10 + (column >> 4))
            # OPTIMIZATION: Slice the buffer and send 16 bytes at once
            # instead of looping 16 times for 1 byte.
            start_index = page * 16
            end_index = start_index + 16
            self.write_data(self.buffer[start_index:end_index])

    def set_invert(self, invert):
        """Set the display to inverted mode using a hardware command."""
        if invert:
            self.write_cmd(0xa7)  # Inverted display
        else:
            self.write_cmd(0xa6)  # Normal display

    def check_button(self):
        """
        Debounced button handler.
        - KEY0: short press -> advance screen by 1
        - KEY1: short press -> toggle timer start/stop
        - KEY1: long press (3s) -> reset timer
        - KEY1: release after long press -> clear alert
        Returns (screen_delta, timer_toggle, timer_reset, clear_alert)
        """
        now = time.ticks_ms()
        k0 = self.key0.value()
        k1 = self.key1.value()

        screen_delta = 0
        timer_toggle = False
        timer_reset = False
        clear_alert = False

        # KEY0 short press: detect falling edge with debounce
        if self._last_key0 == 1 and k0 == 0:
            if time.ticks_diff(now, self._last_time_k0) > self._debounce_ms:
                screen_delta = 1
                self._last_time_k0 = now

        # KEY1 press start
        if self._last_key1 == 1 and k1 == 0:
            if time.ticks_diff(now, self._last_time_k1) > self._debounce_ms:
                self._k1_press_start = now
                self._k1_reset_fired = False

        # KEY1 long press detection while held
        if self._k1_press_start is not None and k1 == 0 and not self._k1_reset_fired:
            press_ms = time.ticks_diff(now, self._k1_press_start)
            if press_ms >= self._longpress_ms:
                timer_reset = True
                self._k1_reset_fired = True

        # KEY1 release: decide short vs long press
        if self._last_key1 == 0 and k1 == 1 and self._k1_press_start is not None:
            press_ms = time.ticks_diff(now, self._k1_press_start)
            if not self._k1_reset_fired and press_ms < self._longpress_ms:
                timer_toggle = True
            if self._k1_reset_fired:
                clear_alert = True
                self._k1_reset_fired = False
            self._k1_press_start = None
            self._last_time_k1 = now

        self._last_key0 = k0
        self._last_key1 = k1

        return screen_delta, timer_toggle, timer_reset, clear_alert
