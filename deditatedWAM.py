from wled import WLED
import asyncio

wled_ip = "192.168.1.106"
led = WLED(wled_ip)

async def main():
    # Connect and get info
    await led.update()
    print(f"Device info: {led.info}")

    # Turn all LEDs on with white
    await led.turn_on()
    await led.set_color((255, 255, 255))

    # Set segment 0 to red
    await led.segments[0].set_color((255, 0, 0))
    await led.update()

asyncio.run(main())
