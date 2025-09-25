from fastapi import FastAPI
import asyncio
import aiohttp

app = FastAPI()
wled_ip = "192.168.1.109"

# Define segments
segments = [{"id": i, "col": [[255, 255, 255]]} for i in range(10)]

# Track current segment states for up and down animations
up_segs = [{"id": seg["id"], "on": False, "bri": 0, "col": seg["col"]} for seg in segments]
down_segs = [{"id": seg["id"], "on": False, "bri": 0, "col": seg["col"]} for seg in segments]

# Track active tasks
up_task: asyncio.Task | None = None
down_task: asyncio.Task | None = None

async def set_segments(final_state):
    async with aiohttp.ClientSession() as session:
        url = f"http://{wled_ip}/json/state"
        try:
            await session.post(url, json={"seg": final_state})
        except Exception as e:
            print(f"Error sending request: {e}")

def merge_segments():
    """Merge up and down segment states."""
    merged = []
    for u, d in zip(up_segs, down_segs):
        bri = max(u["bri"], d["bri"])
        col = u["col"] if u["bri"] >= d["bri"] else d["col"]
        merged.append({"id": u["id"], "on": bri > 0, "bri": bri, "col": col})
    return merged

async def animate_steps(direction="up"):
    global up_segs, down_segs
    seg_order = list(reversed(segments)) if direction == "down" else segments
    seg_states = up_segs if direction == "up" else down_segs
    opposite_segs = down_segs if direction == "up" else up_segs

    for seg in seg_order:
        # Stop if collision detected
        if opposite_segs[seg["id"]]["bri"] > 0:
            break

        seg_states[seg["id"]]["bri"] = 255
        seg_states[seg["id"]]["on"] = True
        await set_segments(merge_segments())
        await asyncio.sleep(0.5)

        seg_states[seg["id"]]["bri"] = 150  # Slight dim
        await set_segments(merge_segments())
        await asyncio.sleep(0.3)

    # Turn off the segments after waiting
    await asyncio.sleep(5)
    for seg in seg_order:
        seg_states[seg["id"]]["bri"] = 0
        seg_states[seg["id"]]["on"] = False
        await set_segments(merge_segments())
        await asyncio.sleep(0.2)

@app.get("/1")
async def bottom_sensor_trigger():
    global up_task
    if up_task is None or up_task.done():
        up_task = asyncio.create_task(animate_steps(direction="up"))
    return {"status": "animation started from bottom"}

@app.get("/2")
async def top_sensor_trigger():
    global down_task
    if down_task is None or down_task.done():
        down_task = asyncio.create_task(animate_steps(direction="down"))
    return {"status": "animation started from top"}
