from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import asyncio
import aiohttp

app = FastAPI()
wled_ip = "192.168.1.108"

# Define segments
segments = [{"id": i, "col": [[255, 255, 255]]} for i in range(10)]

# Track current segment states
up_segs = [{"id": seg["id"], "on": False, "bri": 0, "col": seg["col"]} for seg in segments]
down_segs = [{"id": seg["id"], "on": False, "bri": 0, "col": seg["col"]} for seg in segments]

up_task: asyncio.Task | None = None
down_task: asyncio.Task | None = None

# Store current color
current_color = [255, 255, 255]

async def set_segments(final_state):
    async with aiohttp.ClientSession() as session:
        url = f"http://{wled_ip}/json/state"
        try:
            await session.post(url, json={"seg": final_state})
        except Exception as e:
            print(f"Error sending request: {e}")

def merge_segments():
    merged = []
    for u, d in zip(up_segs, down_segs):
        bri = max(u["bri"], d["bri"])
        col = u["col"] if u["bri"] >= d["bri"] else d["col"]
        merged.append({"id": u["id"], "on": bri > 0, "bri": bri, "col": col})
    return merged

async def animate_steps(direction="up", solid=False, color=None):
    global up_segs, down_segs, current_color
    if color:
        current_color = color

    seg_order = list(reversed(segments)) if direction == "down" else segments
    seg_states = up_segs if direction == "up" else down_segs
    opposite_segs = down_segs if direction == "up" else up_segs

    if solid:
        # Solid mode: light up all at once
        for seg in seg_order:
            seg_states[seg["id"]]["bri"] = 255
            seg_states[seg["id"]]["on"] = True
            seg_states[seg["id"]]["col"] = [current_color]
        await set_segments(merge_segments())
        await asyncio.sleep(3)  # stay on for a while
        # fade out
        for step in range(5, -1, -1):
            for seg in seg_order:
                brightness = int(seg_states[seg["id"]]["bri"] * step / 5)
                seg_states[seg["id"]]["bri"] = brightness
                seg_states[seg["id"]]["on"] = brightness > 0
            await set_segments(merge_segments())
            await asyncio.sleep(0.1)
        return

    # Existing animation code
    collision_index = None
    for seg in seg_order:
        if opposite_segs[seg["id"]]["bri"] > 0:
            collision_index = seg["id"]
            break
        seg_states[seg["id"]]["bri"] = 255
        seg_states[seg["id"]]["on"] = True
        seg_states[seg["id"]]["col"] = [current_color]
        await set_segments(merge_segments())
        await asyncio.sleep(0.9)
        seg_states[seg["id"]]["bri"] = 180
        await set_segments(merge_segments())
        await asyncio.sleep(0.8)

    # Fade-out logic
    fade_order = []
    if collision_index is not None:
        middle = collision_index
        fade_order = [[middle]]
        for offset in range(1, len(segments)):
            group = []
            left = middle - offset
            right = middle + offset
            if left >= 0:
                group.append(left)
            if right < len(segments):
                group.append(right)
            if not group:
                break
            fade_order.append(group)
    else:
        fade_order = [[seg["id"]] for seg in (reversed(seg_order) if direction == "down" else seg_order)]

    await asyncio.sleep(10)
    for group in fade_order:
        for step in range(5, -1, -1):
            for idx in group:
                if up_segs[idx]["on"]:
                    brightness = int(up_segs[idx]["bri"] * step / 5)
                    up_segs[idx]["bri"] = brightness
                    up_segs[idx]["on"] = brightness > 0
                if down_segs[idx]["on"]:
                    brightness = int(down_segs[idx]["bri"] * step / 5)
                    down_segs[idx]["bri"] = brightness
                    down_segs[idx]["on"] = brightness > 0
            await set_segments(merge_segments())
            await asyncio.sleep(0.1) # Adjust fade speed here

async def set_all_lights(on: bool, color=None):
    global up_segs, down_segs, current_color
    if color:
        current_color = color
    for seg in segments:
        up_segs[seg["id"]]["on"] = on
        down_segs[seg["id"]]["on"] = on
        brightness = 255 if on else 0
        up_segs[seg["id"]]["bri"] = brightness
        down_segs[seg["id"]]["bri"] = brightness
        up_segs[seg["id"]]["col"] = [current_color]
        down_segs[seg["id"]]["col"] = [current_color]
    await set_segments(merge_segments())

@app.get("/1")
async def bottom_sensor_trigger(solid: bool = False, r: int = 255, g: int = 255, b: int = 255):
    global up_task
    color = [r, g, b]
    if up_task is None or up_task.done():
        up_task = asyncio.create_task(animate_steps(direction="up", solid=solid, color=color))
    return {"status": "animation started from bottom"}

@app.get("/2")
async def top_sensor_trigger(solid: bool = False, r: int = 255, g: int = 255, b: int = 255):
    global down_task
    color = [r, g, b]
    if down_task is None or down_task.done():
        down_task = asyncio.create_task(animate_steps(direction="down", solid=solid, color=color))
    return {"status": "animation started from top"}

@app.get("/toggle")
async def toggle_lights(on: bool = True, r: int = 255, g: int = 255, b: int = 255):
    color = [r, g, b]
    await set_all_lights(on, color)
    return {"status": f"lights {'on' if on else 'off'}"}

@app.get("/set_color")
async def set_color(r: int = 255, g: int = 255, b: int = 255):
    global current_color
    current_color = [r, g, b]

    # Update current segments with new color
    for seg in segments:
        if up_segs[seg["id"]]["on"]:
            up_segs[seg["id"]]["col"] = [current_color]
        if down_segs[seg["id"]]["on"]:
            down_segs[seg["id"]]["col"] = [current_color]

    await set_segments(merge_segments())
    return {"status": "color updated", "color": current_color}


@app.get("/", response_class=HTMLResponse)
async def home():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Staircase Control</title>
        <style>
            body { font-family: sans-serif; text-align: center; margin-top: 50px; }
            button { font-size: 20px; padding: 20px; margin: 20px; cursor: pointer; }
            input[type=color] { width: 100px; height: 40px; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>Staircase Sensor Simulation</h1>
        <input type="color" id="colorPicker" value="#ffffff" onchange="updateColor()">
<label><input type="checkbox" id="solidMode"> Solid Mode</label><br><br>

        <button onclick="trigger('1')">Bottom Sensor</button>
        <button onclick="trigger('2')">Top Sensor</button>
        <button onclick="toggle(true)">Lights On</button>
        <button onclick="toggle(false)">Lights Off</button>

        <script>
    function hexToRgb(hex) {
        let bigint = parseInt(hex.slice(1), 16);
        let r = (bigint >> 16) & 255;
        let g = (bigint >> 8) & 255;
        let b = bigint & 255;
        return [r, g, b];
    }

    async function updateColor() {
        const color = hexToRgb(document.getElementById("colorPicker").value);
        await fetch(`/set_color?r=${color[0]}&g=${color[1]}&b=${color[2]}`);
    }

    async function trigger(sensor) {
        const color = hexToRgb(document.getElementById("colorPicker").value);
        const solid = document.getElementById("solidMode").checked;
        await fetch(`/${sensor}?solid=${solid}&r=${color[0]}&g=${color[1]}&b=${color[2]}`);
    }

    async function toggle(on) {
        const color = hexToRgb(document.getElementById("colorPicker").value);
        await fetch(`/toggle?on=${on}&r=${color[0]}&g=${color[1]}&b=${color[2]}`);
    }
</script>

    </body>
    </html>
    """
    return HTMLResponse(content=html_content)