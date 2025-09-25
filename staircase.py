import asyncio
import requests

wled_ip = '192.168.1.106'
segments = [
    {"id": i, "col": [[255, 255, 255]]} for i in range(10)
]

async def set_segments(seg_states):
    url = f'http://{wled_ip}/json/state'
    payload = {"seg": seg_states}
    try:
        requests.post(url, json=payload)
    except requests.RequestException as e:
        print(f"Error sending request: {e}")

async def animate_steps():
    # Initialize segment states (all off, medium brightness)
    current_segs = [{"id": seg["id"], "on": False, "bri": 128, "col": seg["col"]} for seg in segments]

    # Turn on segments one by one with brighten-and-dim
    for i in range(len(segments)):
        current_segs[i]["on"] = True

        # Brighten
        current_segs[i]["bri"] = 255
        await set_segments(current_segs)
        await asyncio.sleep(0.7)

        # Slightly dim for dramatic effect
        current_segs[i]["bri"] = 200
        await set_segments(current_segs)
        await asyncio.sleep(0.8)

    # Wait 5 seconds with all segments on
    await asyncio.sleep(5)

    # Turn off segments one by one
    for i in range(len(segments)):
        current_segs[i]["on"] = False
        await set_segments(current_segs)
        await asyncio.sleep(2)

# Run the animation
asyncio.run(animate_steps())
