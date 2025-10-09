import os
import io
import requests
import textwrap
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
from collections import defaultdict
from material_icons import MaterialIcons

# --- Configuration ---
HA_URL = os.environ.get("HA_URL")
HA_TOKEN = os.environ.get("HA_TOKEN")
WEATHER_ENTITY = os.environ.get("WEATHER_ENTITY")
CALENDAR_ENTITY = os.environ.get("CALENDAR_ENTITY")
AI_INSTRUCTIONS = os.environ.get("AI_INSTRUCTIONS")
AI_ENTITY_ID = os.environ.get("AI_ENTITY_ID")
OUTPUT_PATH = "trmnl.png"

# --- Image Settings ---
IMG_WIDTH = 800
IMG_HEIGHT = 480
BG_COLOR = "white"
FONT_COLOR = "black"

# --- Icon Mapping ---
# Maps HA weather conditions to Material Icon names.
# Cheatsheet: https://marella.github.io/material-icons/demo/
# Keys are normalized (lowercase, no hyphens) for consistent matching.
WEATHER_ICON_MAP = {
    "clearnight": "nightlight",
    "cloudy": "cloud",
    "exceptional": "warning",
    "fog": "cloud",
    "hail": "grain",
    "lightning": "flash_on",
    "lightningrainy": "thunderstorm",
    "partlycloudy": "partly_cloudy_day",
    "pouring": "water_drop",
    "rainy": "umbrella",
    "snowy": "ac_unit",
    "snowyrainy": "cloudy_snowing",
    "sunny": "wb_sunny",
    "windy": "air",
    "windyvariant": "air",
}
DEFAULT_ICON = "help_outline" # Icon for unknown conditions

# Initialize the icon provider
icons = MaterialIcons()

def get_font(size, bold=False):
    """Loads a font, falling back to default if not found."""
    try:
        font_name = "arialbd.ttf" if bold else "arial.ttf"
        return ImageFont.truetype(font_name, size)
    except IOError:
        print(f"Arial font not found, falling back to default font.")
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

def get_ai_task_data(entity_id, instructions):
    """Calls the ai_task.generate_data service."""
    if not entity_id or not instructions:
        return None
    return post_ha_data(
        "services/ai_task/generate_data",
        {
            "entity_id": entity_id,
            "task_name": "Interesting Fact", # This can be customized if needed
            "instructions": instructions,
        },
        return_response=True,
    )

def generate_image():
    """Creates the image with weather and calendar data and saves it to a file."""
    img = Image.new("1", (IMG_WIDTH, IMG_HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    # --- Fonts ---
    font_date = get_font(36, bold=True)
    font_regular = get_font(24)
    font_bold = get_font(24, bold=True)
    font_small = get_font(18)

    # --- Draw Date ---
    today = datetime.now()
    date_text = today.strftime("%A, %B %d, %Y")
    # Correctly calculate text width using textbbox and center it
    text_bbox = draw.textbbox((0, 0), date_text, font=font_date)
    text_width = text_bbox[2] - text_bbox[0]
    draw.text(((IMG_WIDTH - text_width) / 2, 20), date_text, font=font_date, fill=FONT_COLOR)


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

        # Weather Icon & Condition Text
        normalized_condition = condition.lower().replace("-", "") if condition else ""
        icon_name = WEATHER_ICON_MAP.get(normalized_condition, DEFAULT_ICON)

        try:
            # Get the icon from the library
            icon_bytes = icons.get(icon_name, size=80, color=FONT_COLOR)
            icon_image = Image.open(io.BytesIO(icon_bytes))
            # Paste the icon, using the icon's alpha channel as a mask for transparency
            img.paste(icon_image, (40, 90), icon_image)
        except Exception as e:
            print(f"Could not load or paste icon '{icon_name}': {e}")
            draw.text((40, 90), "?", font=font_bold, fill=FONT_COLOR) # Fallback character

        if condition != "Unavailable":
             # Display condition text next to the icon, vertically centered
            condition_text = condition.replace("-", " ").title()
            draw.text((140, 125), condition_text, font=font_bold, fill=FONT_COLOR)

        # Weather Numerical Data
        y_start = 200
        draw.text((30, y_start), f"Now: {temp}°", font=font_regular, fill=FONT_COLOR)
        high_text = f"High: {temp_high}°" if temp_high is not None else "High: N/A"
        low_text = f"Low: {temp_low}°" if temp_low is not None else "Low: N/A"
        draw.text((30, y_start + 40), high_text, font=font_regular, fill=FONT_COLOR)
        draw.text((30, y_start + 80), low_text, font=font_regular, fill=FONT_COLOR)

    except Exception as e:
        draw.text((30, 80), "Weather Unavailable", font=font_bold, fill=FONT_COLOR)
        print(f"Error getting weather: {e}")

    # --- Draw Calendar (Right Side) ---
    try:
        if not CALENDAR_ENTITY:
            raise ValueError("CALENDAR_ENTITY is not set.")
        start_date = datetime.utcnow().isoformat()
        end_date = (datetime.utcnow() + timedelta(days=4)).isoformat()
        calendar_data = get_ha_data(f"calendars/{CALENDAR_ENTITY}?start={start_date}Z&end={end_date}Z")

        # Move "Upcoming Events" down to avoid overlap
        draw.text((450, 80), "Upcoming Events", font=font_bold, fill=FONT_COLOR)
        y_pos = 120

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
        draw.text((450, 30), "Calendar Unavailable", font=font_bold, fill=FONT_COLOR)
        print(f"Error getting calendar: {e}")

    # --- Draw AI Task Response (Bottom) ---
    ai_text_to_display = None
    try:
        if AI_ENTITY_ID and AI_INSTRUCTIONS:
            ai_data = get_ai_task_data(AI_ENTITY_ID, AI_INSTRUCTIONS)
            print(f"Raw AI Task Response: {ai_data}") # Log the raw output

            # The response from HA can be a direct service response or a list of updated entities.
            # We need to handle both cases to robustly find the AI's output.

            # Case 1: Direct service response (e.g., from a conversation agent)
            if isinstance(ai_data, dict) and "service_response" in ai_data:
                service_response = ai_data.get("service_response", {})
                # The actual text can be in 'response' or 'data' depending on the agent
                ai_text_to_display = service_response.get("response") or service_response.get("data")

            # Case 2: List of updated entities (e.g., from a task that updates its own state)
            elif isinstance(ai_data, list):
                entity_state = next((s for s in ai_data if s.get("entity_id") == AI_ENTITY_ID), None)
                if entity_state:
                    # The response is often stored in an attribute of the entity
                    ai_text_to_display = entity_state.get("attributes", {}).get("response")

            if not ai_text_to_display:
                # If we got data but couldn't parse it, raise an error to show "Unavailable"
                if ai_data is not None:
                     raise ValueError(f"Could not find a valid AI response in the data: {ai_data}")

        if ai_text_to_display:
            # --- Text Wrapping and Drawing ---
            font_ai = get_font(20)
            # Estimate wrap width based on font and image size
            # This is an approximation; a more accurate way would be to measure character width
            avg_char_width = 11
            wrap_width = (IMG_WIDTH - 60) // avg_char_width # Use image width with padding

            wrapped_text = textwrap.fill(ai_text_to_display, width=wrap_width)

            text_bbox = draw.textbbox((0, 0), wrapped_text, font=font_ai, align="center")
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            # Center the text block horizontally and place it at the bottom
            x_pos = (IMG_WIDTH - text_width) / 2
            y_pos = IMG_HEIGHT - text_height - 20 # 20px padding from the bottom

            draw.text((x_pos, y_pos), wrapped_text, font=font_ai, fill=FONT_COLOR, align="center")

    except Exception as e:
        print(f"Error getting or drawing AI task data: {e}")
        # Display a clear error message on the image if something goes wrong
        error_font = get_font(18)
        error_text = "AI Task Unavailable"
        text_bbox = draw.textbbox((0, 0), error_text, font=error_font)
        text_width = text_bbox[2] - text_bbox[0]
        x_pos = (IMG_WIDTH - text_width) / 2
        draw.text((x_pos, IMG_HEIGHT - 40), error_text, font=error_font, fill=FONT_COLOR)


    # --- Save image to file ---
    img.save(OUTPUT_PATH)
    print(f"Image saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    # AI variables are optional, so they are not included in the check
    if not all([HA_URL, HA_TOKEN, WEATHER_ENTITY, CALENDAR_ENTITY]):
        raise ValueError("One or more required environment variables are not set.")
    generate_image()