import asyncio
import requests

# === Configuration ===
wled_ip = '192.168.1.106'
segments_count = 10
lux_threshold = 50  # Don't turn on if lux is above this value

# Define your segments (adjust ranges if necessary)
segments = [{"id": i, "col": [[255, 255, 255]]} for i in range(segments_count)]

# Flag to prevent overlapping animations
is_animating = False

# === Function to send segment states to WLED ===
async def set_segments(seg_states):
    url = f'http://{wled_ip}/json/state'
    payload = {"seg": seg_states}
    try:
        requests.post(url, json=payload)
    except requests.RequestException as e:
        print(f"Error sending request: {e}")

# === Animation function ===
async def animate_steps(sensor_side="bottom", lux=0):
    global is_animating
    if is_animating:
        print("Animation already running, ignoring trigger.")
        return
    if lux > lux_threshold:
        print(f"Room too bright (lux={lux}), skipping animation.")
        return

    is_animating = True
    print(f"Starting animation from {sensor_side} side with lux={lux}")

    # Determine direction based on sensor side
    indices = range(len(segments))
    if sensor_side.lower() == "top":
        indices = reversed(indices)

    # Initialize segments off
    current_segs = [{"id": seg["id"], "on": False, "bri": 128, "col": seg["col"]} for seg in segments]

    # Turn on segments one by one with brighten-and-dim
    for i in indices:
        current_segs[i]["on"] = True

        # Brighten
        current_segs[i]["bri"] = 255
        await set_segments(current_segs)
        await asyncio.sleep(0.5)

        # Slightly dim for effect
        current_segs[i]["bri"] = 200
        await set_segments(current_segs)
        await asyncio.sleep(0.5)

    # Wait with all segments on
    await asyncio.sleep(5)

    # Turn off segments one by one
    for i in indices:
        current_segs[i]["on"] = False
        await set_segments(current_segs)
        await asyncio.sleep(0.5)

    print("Animation complete")
    is_animating = False

# === Example usage ===
# Call this function with sensor_side="bottom" or "top" and lux value
# asyncio.run(animate_steps(sensor_side="bottom", lux=20))
