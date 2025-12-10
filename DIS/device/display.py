from writer import Writer
from fonts import font_digits_large, font_digits_med, font_letters_large
import time

class DisplayManager:
    def __init__(self, oled_driver):
        self.oled = oled_driver
        self.width = oled_driver.width
        self.height = oled_driver.height

        # --- Custom Font Writers ----
        self.w_digits_large = Writer(self.oled, font_digits_large, verbose=False)
        self.w_digits_med = Writer(self.oled, font_digits_med, verbose=False)
        self.w_letters_big = Writer(self.oled, font_letters_large, verbose=False)

        self.w_digits_large.set_wrap(False)
        self.w_digits_med.set_wrap(False)

        # ---- Precompute fixed slot positions for DD.D ----
        self._big_slot_x0 = 9  # tens
        self._big_slot_x1 = 43  # ones
        self._big_slot_xdot = 79  # '.'
        self._big_slot_x2 = 93  # tenths
        self._big_slot_y = 0

        # ---- Precompute fixed slot positions for MM:SS ----
        dmed = self.w_digits_med.stringlen("0")
        colon_w = self.w_digits_med.stringlen(":")
        x0m = -4
        self._time_x_m10 = x0m
        self._time_x_m1 = self._time_x_m10 + dmed - 4
        self._time_x_colon = self._time_x_m1 + dmed - 4
        self._time_x_s10 = self._time_x_colon + colon_w - 22
        self._time_x_s1 = self._time_x_s10 + dmed - 4
        self._time_y = 5

        #--------- Alert State ----------------
        self._msg_top = None
        self._msg_bottom = None
        self._msg_until = 0  # ms timestamp; 0 means no active message
        self._is_inverted = False
        self._screen_changed = True

    def _set_inversion(self, invert):
        """Internal helper to manage hardware inversion state."""
        if invert != self._is_inverted:
            self.oled.set_invert(invert)
            self._is_inverted = invert

    def screen_changed(self):
        """Signals that the screen has changed and a full redraw is needed."""
        self._screen_changed = True

    def draw_large_num(self, num, label, uart_blink, timer_state, invert=False, eco=False):
        """
        Draw speed as fixed DD.D using precomputed slots.
        Set invert=True to flip colors before showing.
        """
        self._set_inversion(invert)

        if self._screen_changed:
            self.oled.fill(0)
            label_x = self.width - len(label) * 8
            label_y = self.height - 8
            self.oled.text(label, label_x, label_y, 1)

        # Clamp range
        if num < 0: num = 0.0
        if num > 99.9: num = 99.9

        int_part = int(num)
        tenths = int((num * 10) % 10)
        ones = int_part % 10
        tens = int_part // 10

        # --- DYNAMIC: Number Area ---
        number_height = self.w_digits_large.height
        self.oled.fill_rect(0, 0, self.width, number_height, 0)

        y = self._big_slot_y

        # Tens digit (only if >= 10.0)
        if tens > 0:
            self.w_digits_large.set_textpos(self._big_slot_x0, y)
            self.w_digits_large.printstring(str(tens))

        # Ones digit
        self.w_digits_large.set_textpos(self._big_slot_x1, y)
        self.w_digits_large.printstring(str(ones))

        # Decimal point
        self.w_digits_large.set_textpos(self._big_slot_xdot, y)
        self.w_digits_large.printstring(".")

        # Tenths digit
        self.w_digits_large.set_textpos(self._big_slot_x2, y)
        self.w_digits_large.printstring(str(tenths))

        # --- DYNAMIC: Status Area ---
        self.draw_status(uart_blink, timer_state)

        # --- DYNAMIC: Eco Line ---
        eco_line_y = self.height - 12
        self.oled.hline(0, eco_line_y, self.width, 0)
        if eco:
            self.oled.line(0, eco_line_y, self.width, eco_line_y, 1)

        self.oled.show()
        self._screen_changed = False

    def draw_time(self, seconds, label, uart_blink, timer_state):
        """
        Draw elapsed time as MM:SS using the medium digit font.
        """
        self._set_inversion(False)
        if self._screen_changed:
            self.oled.fill(0)
            label_x = self.width - len(label) * 8
            label_y = self.height - 8
            self.oled.text(label, label_x, label_y, 1)

        if seconds < 0: seconds = 0
        total = int(seconds)

        max_total = 99 * 60 + 59
        if total > max_total: total = max_total

        mins = total // 60
        secs = total % 60

        m10 = mins // 10
        m1 = mins % 10
        s10 = secs // 10
        s1 = secs % 10

        # --- DYNAMIC: Time Area ---
        time_height = self.w_digits_med.height
        self.oled.fill_rect(0, 0, self.width, time_height, 0)

        y = self._time_y

        # Minutes (tens and ones)
        self.w_digits_med.set_textpos(self._time_x_m10, y)
        self.w_digits_med.printstring(str(m10))
        self.w_digits_med.set_textpos(self._time_x_m1, y)
        self.w_digits_med.printstring(str(m1))

        # Colon
        self.w_digits_med.set_textpos(self._time_x_colon, y - 7)
        self.w_digits_med.printstring(":")

        # Seconds (tens and ones)
        self.w_digits_med.set_textpos(self._time_x_s10, y)
        self.w_digits_med.printstring(str(s10))
        self.w_digits_med.set_textpos(self._time_x_s1, y)
        self.w_digits_med.printstring(str(s1))

        # --- DYNAMIC: Status Area ---
        self.draw_status(uart_blink, timer_state)
        self.oled.show()
        self._screen_changed = False

    def draw_demo_distance(self, distance):
        """Draw distance that caps at out .999 for demo purposes only"""
        # This screen has no other dynamic elements, so a full redraw is simpler.
        self._set_inversion(False)
        self.oled.fill(0)
        distance = max(0, min(int(distance * 1000), 999))

        n1 = distance // 100
        n2 = (distance // 10) % 10
        n3 = distance % 10

        y = self._big_slot_y

        self.w_digits_large.set_textpos(0, y)
        self.w_digits_large.printstring(".")
        self.w_digits_large.set_textpos(14, y)
        self.w_digits_large.printstring(str(n1))
        self.w_digits_large.set_textpos(53, y)
        self.w_digits_large.printstring(str(n2))
        self.w_digits_large.set_textpos(91, y)
        self.w_digits_large.printstring(str(n3))

        label = "MILES"
        label_x = self.width - len(label) * 8
        label_y = self.height - 8
        self.oled.text(label, label_x, label_y, 1)

        self.oled.show()
        self._screen_changed = False

    def draw_status(self, uart_blink, timer_state):
        """
        Draw UART and timer indicators on the bottom row.
        """
        y = self.height - 8
        self.oled.fill_rect(0, y, 40, 8, 0)

        if uart_blink:
            self.oled.text("U", 0, y, 1)

        x_rec = 11
        if timer_state == "running":
            self.oled.fill_rect(x_rec - 1, y - 1, 26, 10, 1)
            self.oled.text("REC", x_rec, y, 0)
        elif timer_state == "paused":
            self.oled.text("REC", x_rec, y, 1)

    def draw_alert(self, top, bottom):
        """
        Draw two words in the letter font, centered.
        """
        self._set_inversion(False)
        self.oled.fill(0)
        if top:
            top = top.upper()
            x_top = max(0, (self.width - self.w_letters_big.stringlen(top)) // 2)
            self.w_letters_big.set_textpos(x_top, 0)
            self.w_letters_big.printstring(top)
        if bottom:
            bottom = bottom.upper()
            x_bottom = max(0, (self.width - self.w_letters_big.stringlen(bottom)) // 2)
            self.w_letters_big.set_textpos(x_bottom, 24)
            self.w_letters_big.printstring(bottom)
        self.oled.show()

    def show_alert(self, top, bottom, seconds):
        """
        Schedule an alert for a certain amount of seconds.
        """
        ms = int(seconds * 1000)
        now = time.ticks_ms()
        self._msg_top = top
        self._msg_bottom = bottom
        self._msg_until = time.ticks_add(now, ms)
        print(f"Alert: {top or ''} {bottom or ''}")

    def clear_alert(self):
        """Clear any active alert immediately."""
        self._msg_top = None
        self._msg_bottom = None
        self._msg_until = 0

    def update_alert(self):
        """
        If an alert is active, draw it and return True. Otherwise, return False.
        """
        if self._msg_top is None:
            return False

        now = time.ticks_ms()
        if time.ticks_diff(self._msg_until, now) <= 0:
            self.clear_alert()
            return False

        self.draw_alert(self._msg_top, self._msg_bottom)
        return True