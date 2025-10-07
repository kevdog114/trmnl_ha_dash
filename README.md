# trmnl_ha_dash

This repository contains configurations for the `trmnl` e-paper display, integrated with Home Assistant. It offers two distinct modes of operation:

1.  **Standalone ESPHome Display:** The default `trmnl.yaml` configuration runs directly on the ESP32 device. It fetches the time from Home Assistant and displays it.
2.  **Dynamic Image Generator (for `trmnl` plugins):** A separate Python service that generates a dynamic image with weather and calendar data from Home Assistant. This image is designed to be used with the `trmnl` redirect plugin.

---

## Option 1: Standalone ESPHome Display

This is the default mode. The configuration is defined in `trmnl.yaml`.

### Features
- Displays the current date and time.
- All rendering is done directly on the ESP32 device.

### Setup
1.  Configure your Wi-Fi credentials in `trmnl.yaml` or a `secrets.yaml` file.
2.  Compile and upload the firmware to your ESP32 device using ESPHome.

---

## Option 2: Dynamic Image Generator Service

This is an advanced option that provides a richer display by offloading the image generation to a separate web service. The service fetches weather and calendar information from your Home Assistant instance and renders it into a PNG image.

### Features
- **Left Side:** Displays the current weather forecast (current temperature, high/low, and condition).
- **Right Side:** Displays upcoming calendar events.
- Designed to be used with the `trmnl` redirect plugin, which points to this service's URL.

### Setup and Configuration

The image generator is a Python Flask application located in the `image_generator/` directory. It is designed to be run as a Docker container.

**1. Configure Your Secrets:**

You must provide your Home Assistant details to the service via environment variables. A template is provided in `image_generator/.env.example`.

First, copy the example file to a new `.env` file:
```bash
cp image_generator/.env.example image_generator/.env
```

Next, edit `image_generator/.env` with your specific details:

```ini
# Home Assistant Configuration
HA_URL=http://homeassistant.local:8123
HA_TOKEN=YOUR_LONG_LIVED_ACCESS_TOKEN
WEATHER_ENTITY=weather.your_weather_entity
CALENDAR_ENTITY=calendar.your_calendar_entity
```

- `HA_URL`: The full URL to your Home Assistant instance.
- `HA_TOKEN`: A Long-Lived Access Token for the Home Assistant API.
- `WEATHER_ENTITY`: The entity ID for your weather forecast.
- `CALENDAR_ENTITY`: The entity ID for the calendar you want to display.

**Important:** The `.env` file contains sensitive information. It is included in `.gitignore` to prevent accidental commits.

**2. Build and Run the Docker Container:**

Navigate to the root of the repository and run the following commands:

```bash
# 1. Build the Docker image
docker build -t trmnl-image-generator -f image_generator/Dockerfile .

# 2. Run the container
docker run -d --name trmnl-server --restart always -p 5001:5001 --env-file image_generator/.env trmnl-image-generator
```
This will:
- Build the Docker image with the tag `trmnl-image-generator`.
- Start a container named `trmnl-server` in detached mode (`-d`).
- Set it to always restart.
- Map port 5001 on your host to port 5001 in the container.
- Load the environment variables from your `.env` file.

### Usage

Once the container is running, the image will be available at:
`http://<IP_ADDRESS_OF_DOCKER_HOST>:5001/image.png`

You can use this URL with the `trmnl` redirect plugin to display it on your device.