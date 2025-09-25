from fastapi import FastAPI
import asyncio
import aiohttp

app = FastAPI()

wled_ip = "192.168.1.109"

# Define segments (adjust according to your setup)
segments = [
    {"id": i, "col": [[255, 255, 255]]} for i in range(10)
]

async def set_segments(seg_states):
    """Send segment states to WLED."""
    async with aiohttp.ClientSession() as session:
        url = f"http://{wled_ip}/json/state"
        try:
            await session.post(url, json={"seg": seg_states})
        except Exception as e:
            print(f"Error sending request: {e}")

async def animate_steps(direction="up"):
    """Animate the steps up or down the staircase."""
    if direction == "down":
        seg_order = list(reversed(segments))  # Top sensor triggers downward animation
    else:
        seg_order = segments  # Bottom sensor triggers upward animation

    current_segs = [{"id": seg["id"], "on": False, "bri": 128, "col": seg["col"]} for seg in segments]

    # Turn on segments one by one
    for seg in seg_order:
        current_segs[seg["id"]]["on"] = True
        current_segs[seg["id"]]["bri"] = 255
        await set_segments(current_segs)
        await asyncio.sleep(0.5)  # Delay between steps

        # Slightly dim for dramatic effect
        current_segs[seg["id"]]["bri"] = 200
        await set_segments(current_segs)
        await asyncio.sleep(0.3)

    # Wait a bit before turning off
    await asyncio.sleep(5)

    # Turn off segments in same order
    for seg in seg_order:
        current_segs[seg["id"]]["on"] = False
        await set_segments(current_segs)
        await asyncio.sleep(0.2)

@app.get("/bottom-sensor")
async def bottom_sensor_trigger():
    """Triggered when someone starts from the bottom."""
    asyncio.create_task(animate_steps(direction="up"))
    return {"status": "animation started from bottom"}

@app.get("/top-sensor")
async def top_sensor_trigger():
    """Triggered when someone starts from the top."""
    asyncio.create_task(animate_steps(direction="down"))
    return {"status": "animation started from top"}
