# trmnl_ha_dash

This repository contains configurations for the `trmnl` e-paper display, integrated with Home Assistant. It offers two distinct modes of operation:

1.  **Standalone ESPHome Display:** The default `trmnl.yaml` configuration runs directly on the ESP32 device. It fetches the time from Home Assistant and displays it.
2.  **Dynamic Image via GitHub Actions:** A Python script, run automatically by a GitHub Action, generates a dynamic image with weather and calendar data from Home Assistant. This image (`trmnl.png`) is committed back to the repository and can be displayed by your `trmnl` device.

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

## Option 2: Dynamic Image via GitHub Actions

This option uses a Python script and a GitHub Action to automatically generate and update an image (`trmnl.png`) in this repository. The image contains weather and calendar information from your Home Assistant instance.

### Features
- **Automated:** A GitHub Action runs every 15 minutes to refresh the image.
- **Serverless:** No need to run your own web server or Docker container.
- **Rich Display:**
    - **Left Side:** Displays the current weather forecast.
    - **Right Side:** Displays upcoming calendar events.

### Setup and Configuration

The image generation is handled by the script in `image_generator/app.py`. To make it work, you must configure secrets in your GitHub repository.

**1. Create GitHub Repository Secrets:**

In your forked repository on GitHub, go to **Settings > Secrets and variables > Actions**. Create the following four repository secrets:

-   `HA_URL`: The full public URL to your Home Assistant instance (e.g., `https://my-home.duckdns.org`).
-   `HA_TOKEN`: A Long-Lived Access Token for the Home Assistant API.
-   `WEATHER_ENTITY`: The entity ID for your weather forecast (e.g., `weather.home`).
-   `CALENDAR_ENTITY`: The entity ID for the calendar you want to display (e.g., `calendar.birthdays`).

**2. Enable GitHub Actions:**

If you forked this repository, you may need to enable GitHub Actions. Go to the **Actions** tab in your repository and enable them if prompted.

**3. Trigger the Action:**

The action will run automatically every 15 minutes. You can also trigger it manually by going to the **Actions** tab, clicking on the **Generate Dashboard Image** workflow, and using the **Run workflow** button.

### Usage

Once the action has run successfully, a `trmnl.png` file will be present in the root of your repository. To use this image with your `trmnl` device, you need its raw URL.

You can get the URL by navigating to the `trmnl.png` file on GitHub and clicking the **Download** or **Raw** button. The URL will look something like this:

`https://raw.githubusercontent.com/YOUR_USERNAME/trmnl_ha_dash/main/trmnl.png`

Use this URL with the `trmnl` redirect plugin to display it on your device.