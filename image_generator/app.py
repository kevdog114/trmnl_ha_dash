import os
import requests
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from datetime import datetime, timedelta

app = Flask(__name__)

# --- Configuration ---
HA_URL = os.environ.get("HA_URL", "http://homeassistant.local:8123")
HA_TOKEN = os.environ.get("HA_TOKEN")
WEATHER_ENTITY = os.environ.get("WEATHER_ENTITY")
CALENDAR_ENTITY = os.environ.get("CALENDAR_ENTITY")

# --- Image Settings ---
IMG_WIDTH = 880
IMG_HEIGHT = 528
BG_COLOR = "white"
FONT_COLOR = "black"
RED_COLOR = "red"
try:
    FONT = ImageFont.truetype("arial.ttf", 24)
    FONT_BOLD = ImageFont.truetype("arialbd.ttf", 24)
except IOError:
    FONT = ImageFont.load_default()
    FONT_BOLD = ImageFont.load_default()


def get_ha_data(endpoint):
    """Fetches data from Home Assistant API."""
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "content-type": "application/json",
    }
    response = requests.get(f"{HA_URL}/api/{endpoint}", headers=headers)
    response.raise_for_status()
    return response.json()


def create_image():
    """Creates the image with weather and calendar data."""
    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    # --- Draw Weather (Left Side) ---
    try:
        weather_data = get_ha_data(f"states/{WEATHER_ENTITY}")
        forecast = weather_data.get("attributes", {}).get("forecast", [])[0]
        temp = weather_data.get("attributes", {}).get("temperature")
        condition = forecast.get("condition")
        temp_high = forecast.get("temperature")
        temp_low = forecast.get("templow")

        draw.text((30, 30), "Weather", font=FONT_BOLD, fill=FONT_COLOR)
        draw.text((30, 70), f"Now: {temp}°", font=FONT, fill=FONT_COLOR)
        draw.text((30, 110), f"High: {temp_high}°", font=FONT, fill=RED_COLOR)
        draw.text((30, 150), f"Low: {temp_low}°", font=FONT, fill=FONT_COLOR)
        draw.text((30, 190), f"Condition: {condition}", font=FONT, fill=FONT_COLOR)
    except Exception as e:
        draw.text((30, 30), "Weather Unavailable", font=FONT_BOLD, fill=RED_COLOR)
        print(f"Error getting weather: {e}")


    # --- Draw Calendar (Right Side) ---
    try:
        start_date = datetime.utcnow().isoformat()
        end_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
        calendar_data = get_ha_data(f"calendars/{CALENDAR_ENTITY}?start={start_date}Z&end={end_date}Z")

        draw.text((450, 30), "Upcoming Events", font=FONT_BOLD, fill=FONT_COLOR)
        y_pos = 70
        if calendar_data:
            for event in calendar_data[:5]: # Display top 5 events
                summary = event.get("summary", "No Title")
                start = event.get("start", {}).get("dateTime", "")
                if start:
                    start_dt = datetime.fromisoformat(start)
                    time_str = start_dt.strftime("%I:%M %p")
                    draw.text((450, y_pos), f"- {summary} at {time_str}", font=FONT, fill=FONT_COLOR)
                else:
                    draw.text((450, y_pos), f"- {summary}", font=FONT, fill=FONT_COLOR)
                y_pos += 40
        else:
            draw.text((450, 70), "No upcoming events.", font=FONT, fill=FONT_COLOR)
    except Exception as e:
        draw.text((450, 30), "Calendar Unavailable", font=FONT_BOLD, fill=RED_COLOR)
        print(f"Error getting calendar: {e}")


    # --- Save image to buffer ---
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


@app.route("/image.png")
def serve_image():
    """Endpoint to serve the generated image."""
    if not all([HA_TOKEN, WEATHER_ENTITY, CALENDAR_ENTITY]):
        return "Missing environment variables for Home Assistant configuration.", 500
    try:
        image_buffer = create_image()
        return send_file(image_buffer, mimetype="image/png")
    except Exception as e:
        return f"Error generating image: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)