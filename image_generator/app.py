import os
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
from collections import defaultdict

# --- Configuration ---
HA_URL = os.environ.get("HA_URL")
HA_TOKEN = os.environ.get("HA_TOKEN")
WEATHER_ENTITY = os.environ.get("WEATHER_ENTITY")
CALENDAR_ENTITY = os.environ.get("CALENDAR_ENTITY")
OUTPUT_PATH = "trmnl.png"

# --- Image Settings ---
IMG_WIDTH = 880
IMG_HEIGHT = 528
BG_COLOR = "white"
FONT_COLOR = "black"
RED_COLOR = "red"

# --- Icon Mapping ---
# Maps HA weather conditions to Material Design Icon codepoints.
# Cheatsheet: https://github.com/Templarian/MaterialDesign-Font/blob/master/cheatsheet.html
WEATHER_ICON_MAP = {
    "clear-night": "\U000F0594",  # weather-night
    "cloudy": "\U000F0595",  # weather-cloudy
    "exceptional": "\U000F0B91",  # weather-sunny-alert
    "fog": "\U000F0596",  # weather-fog
    "hail": "\U000F0597",  # weather-hail
    "lightning": "\U000F0598",  # weather-lightning
    "lightning-rainy": "\U000F067E",  # weather-lightning-rainy
    "partlycloudy": "\U000F0599",  # weather-partly-cloudy
    "pouring": "\U000F059A",  # weather-pouring
    "rainy": "\U000F059B",  # weather-rainy
    "snowy": "\U000F059C",  # weather-snowy
    "snowy-rainy": "\U000F067F",  # weather-snowy-rainy
    "sunny": "\U000F059D",  # weather-sunny
    "windy": "\U000F059E",  # weather-windy
    "windy-variant": "\U000F059F",  # weather-windy-variant
}
DEFAULT_ICON = "\U000F0B91" # weather-sunny-alert for unknown conditions


def get_font(size, bold=False):
    """Loads a font, falling back to default if not found."""
    try:
        font_name = "arialbd.ttf" if bold else "arial.ttf"
        return ImageFont.truetype(font_name, size)
    except IOError:
        print(f"Arial font not found, falling back to default font.")
        return ImageFont.load_default()

def get_icon_font(size):
    """Loads the icon font."""
    try:
        # Construct an absolute path to the font file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(script_dir, "MaterialDesignIconsDesktop.ttf")
        return ImageFont.truetype(font_path, size)
    except IOError:
        print("Icon font not found, using default font for icons.")
        return ImageFont.load_default()


def get_ha_data(endpoint):
    """Fetches data from Home Assistant API."""
    if not HA_TOKEN:
        raise ValueError("HA_TOKEN is not set.")
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "content-type": "application/json",
    }
    response = requests.get(f"{HA_URL}/api/{endpoint}", headers=headers)
    response.raise_for_status()
    return response.json()

def post_ha_data(endpoint, data, return_response=False):
    """Posts data to Home Assistant API."""
    if not HA_TOKEN:
        raise ValueError("HA_TOKEN is not set.")
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "content-type": "application/json",
    }
    url = f"{HA_URL}/api/{endpoint}"
    if return_response:
        url += "?return_response"
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def get_ha_forecast(entity_id):
    """Fetches weather forecast using the weather.get_forecasts service."""
    return post_ha_data(
        "services/weather/get_forecasts",
        {"entity_id": entity_id, "type": "twice_daily"},
        return_response=True,
    )

def generate_image():
    """Creates the image with weather and calendar data and saves it to a file."""
    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    # --- Fonts ---
    font_date = get_font(36, bold=True)
    font_regular = get_font(24)
    font_bold = get_font(24, bold=True)
    font_small = get_font(18)
    icon_font = get_icon_font(80) # Larger size for the icon

    # --- Draw Date ---
    today = datetime.now()
    date_text = today.strftime("%A, %B %d, %Y")
    draw.text((30, 20), date_text, font=font_date, fill=FONT_COLOR)


    # --- Draw Weather (Left Side) ---
    try:
        if not WEATHER_ENTITY:
            raise ValueError("WEATHER_ENTITY is not set.")

        # Fetch current weather state for current temperature
        weather_data = get_ha_data(f"states/{WEATHER_ENTITY}")
        temp = weather_data.get("attributes", {}).get("temperature")

        # Fetch forecast
        forecast_data = get_ha_forecast(WEATHER_ENTITY)
        service_response = forecast_data.get("service_response", {})
        forecast_list = service_response.get(WEATHER_ENTITY, {}).get("forecast", [])

        temp_high = None
        temp_low = None
        condition = "Unavailable"

        if forecast_list:
            condition = forecast_list[0].get("condition")

            day_forecast = next((f for f in forecast_list if f.get("is_daytime")), None)
            night_forecast = next((f for f in forecast_list if not f.get("is_daytime")), None)

            if day_forecast:
                temp_high = day_forecast.get("temperature")
            if night_forecast:
                temp_low = night_forecast.get("temperature")

            # Fallback if one is missing
            if temp_high is None and temp_low is not None:
                temp_high = temp_low
            if temp_low is None and temp_high is not None:
                temp_low = temp_high

        # Weather Icon
        weather_icon = WEATHER_ICON_MAP.get(condition.lower(), DEFAULT_ICON) if condition else DEFAULT_ICON
        draw.text((40, 80), weather_icon, font=icon_font, fill=FONT_COLOR)

        # Weather Text
        y_start = 180
        draw.text((30, y_start), f"Now: {temp}°", font=font_regular, fill=FONT_COLOR)
        high_text = f"High: {temp_high}°" if temp_high is not None else "High: N/A"
        low_text = f"Low: {temp_low}°" if temp_low is not None else "Low: N/A"
        draw.text((30, y_start + 40), high_text, font=font_regular, fill=RED_COLOR)
        draw.text((30, y_start + 80), low_text, font=font_regular, fill=FONT_COLOR)

    except Exception as e:
        draw.text((30, 80), "Weather Unavailable", font=font_bold, fill=RED_COLOR)
        print(f"Error getting weather: {e}")

    # --- Draw Calendar (Right Side) ---
    try:
        if not CALENDAR_ENTITY:
            raise ValueError("CALENDAR_ENTITY is not set.")
        start_date = datetime.utcnow().isoformat()
        end_date = (datetime.utcnow() + timedelta(days=4)).isoformat()
        calendar_data = get_ha_data(f"calendars/{CALENDAR_ENTITY}?start={start_date}Z&end={end_date}Z")

        draw.text((450, 30), "Upcoming Events", font=font_bold, fill=FONT_COLOR)
        y_pos = 70

        if calendar_data:
            # Group events by date
            events_by_date = defaultdict(list)
            for event in calendar_data:
                start = event.get("start", {})
                event_date = None
                if "dateTime" in start and start["dateTime"]:
                    start_dt = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00"))
                    event_date = start_dt.date()
                elif "date" in start and start["date"]:
                    event_date = datetime.fromisoformat(start["date"]).date()

                if event_date:
                    events_by_date[event_date].append(event)

            # Sort dates and display events
            sorted_dates = sorted(events_by_date.keys())
            font_date = get_font(22, bold=True)
            font_event = get_font(18)

            for event_date in sorted_dates:
                if y_pos > IMG_HEIGHT - 50: break # Stop if we run out of space

                # Display the date
                draw.text((450, y_pos), event_date.strftime("%A, %B %d"), font=font_date, fill=FONT_COLOR)
                y_pos += 30

                # Display events for that date
                for event in events_by_date[event_date]:
                    if y_pos > IMG_HEIGHT - 40: break
                    summary = event.get("summary", "No Title")
                    start = event.get("start", {})

                    if "dateTime" in start and start["dateTime"]:
                        start_dt = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00"))
                        time_str = start_dt.strftime("%I:%M %p")
                        event_text = f"- {summary} at {time_str}"
                    else: # All-day event
                        event_text = f"- {summary}"

                    draw.text((460, y_pos), event_text, font=font_event, fill=FONT_COLOR)
                    y_pos += 25
                y_pos += 10 # Add a little space between dates

        else:
            draw.text((450, 70), "No upcoming events.", font=font_regular, fill=FONT_COLOR)
    except Exception as e:
        draw.text((450, 30), "Calendar Unavailable", font=font_bold, fill=RED_COLOR)
        print(f"Error getting calendar: {e}")

    # --- Save image to file ---
    img.save(OUTPUT_PATH)
    print(f"Image saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    if not all([HA_URL, HA_TOKEN, WEATHER_ENTITY, CALENDAR_ENTITY]):
        raise ValueError("One or more required environment variables are not set.")
    generate_image()