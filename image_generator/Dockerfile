# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install fonts for Pillow
RUN apt-get update && apt-get install -y libopenjp2-7-dev libtiff-dev libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev ttf-mscorefonts-installer fontconfig && \
    fc-cache -f -v

# Copy the rest of the application's code into the container at /app
COPY . .

# Make port 5001 available to the world outside this container
EXPOSE 5001

# Define environment variables (can be overridden at runtime)
ENV HA_URL="http://homeassistant.local:8123"
ENV HA_TOKEN=""
ENV WEATHER_ENTITY=""
ENV CALENDAR_ENTITY=""

# Run app.py when the container launches
CMD ["python", "app.py"]