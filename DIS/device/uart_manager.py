class UartManager:
    def __init__(self, uart_instance):
        self.uart = uart_instance
        self.buffer = ""

        # Live values
        self.voltage = 0.0
        self.current = 0.0
        self.rpm = 0
        self.duty = 0
        self.throttle = 0.0
        self.eco = False
        self.uart_blink = False
        self.new_data = False # Flag to indicate if new data was parsed

    def update(self):
        """
        Reads from UART, parses messages, and updates internal state.
        Should be called once per main loop iteration.
        """
        self.new_data = False
        if self.uart.any():
            data = self.uart.read()
            if data:
                # Convert bytes to printable characters
                for b in data:
                    if 32 <= b <= 126 or b == 10:
                        self.buffer += chr(b)

                # Process complete lines
                while "\n" in self.buffer:
                    line, self.buffer = self.buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue

                    self._parse_line(line)
                    self.new_data = True
                    self.uart_blink = not self.uart_blink

    def _parse_line(self, line):
        """Parses a single line of data from the UART."""
        try:
            if line.startswith("s"):
                self.voltage = float(line[1:4]) / 10
                self.current = float(line[4:10]) / 1000
                self.rpm = int(line[10:13])
                self.duty = int(line[13:16])
                self.throttle = int(line[16:19])
                self.eco = bool(int(line[19:]))
        except Exception as e:
            print("Parse error:", e, "on line:", line)