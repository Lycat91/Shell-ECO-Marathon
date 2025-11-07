import uasyncio
from machine import Pin

pin = Pin("LED", Pin.OUT)

async def blink():
    while True:
        pin.value(not pin.value())
        print(pin.value())
        await uasyncio.sleep(3)

async def main():
    uasyncio.create_task(blink())
    await uasyncio.sleep(1)

uasyncio.run(main())


    