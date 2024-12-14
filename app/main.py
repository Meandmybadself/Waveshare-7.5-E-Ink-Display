import sys
import os
import textwrap
from dotenv import load_dotenv
import requests
import json
from datetime import datetime
import time
from PIL import Image, ImageDraw, ImageFont
import traceback
import logging
import RPi.GPIO as GPIO

# Initialize logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.debug("Environment variables loaded")

# Configuration and Setup
#----------------------------------------
# Set up directory paths for resources
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')

logger.debug(f"Picture directory: {picdir}")
logger.debug(f"Library directory: {libdir}")

# Add lib directory to system path if it exists
if os.path.exists(libdir):
    sys.path.append(libdir)
    logger.debug(f"Added {libdir} to system path")
else:
    logger.warning(f"Library directory {libdir} does not exist")

def check_spi_access():
    """Check if SPI devices are accessible – if they arent, run raspi-config to enable SPI"""
    spi_devices = ['/dev/spidev0.0', '/dev/spidev0.1']
    for device in spi_devices:
        if not os.access(device, os.R_OK | os.W_OK):
            logger.error(f"No read/write access to {device}")
            return False
    return True

# Add this before initializing the display
if not check_spi_access():
    logger.error("SPI access check failed. Please check raspi-config and group membership.")
    sys.exit(1)

logger.debug("Importing E-Ink display module")
from waveshare_epd import epd7in5_V2
logger.debug("E-Ink display module imported")

# Load environment variables for aircraft tracking
LATITUDE = os.getenv('LATITUDE')
LONGITUDE = os.getenv('LONGITUDE')
RADIUS = os.getenv('RADIUS')

logger.debug(f"Configured tracking parameters - LAT: {LATITUDE}, LON: {LONGITUDE}, RADIUS: {RADIUS}")

# API Functions
#----------------------------------------
def get_closest_aircraft():
    """
    Fetch data about the closest aircraft from the ADSB API
    Returns: Dictionary with aircraft data or None if request fails
    """
    logger.debug("Attempting to fetch closest aircraft data")
    try:
        url = f'https://api.adsb.lol/v2/closest/{LATITUDE}/{LONGITUDE}/{RADIUS}'
        logger.debug(f"Making API request to: {url}")
        
        response = requests.get(url)
        logger.debug(f"API response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.debug(f"Received aircraft data: {json.dumps(data, indent=2)}")
            
            # Check if we have any aircraft in the response
            if data.get('ac') and len(data['ac']) > 0:
                # Return the first aircraft in the array
                return data['ac'][0]
            else:
                logger.warning("No aircraft found in response")
                return None
                
        else:
            logger.error(f"API request failed with status code: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"API request failed with exception: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def update_display(aircraft_data):
    """
    Update the E-Ink display with aircraft information
    Args:
        aircraft_data: Dictionary containing aircraft information
    """
    epd = None
    logger.debug("Starting display update")
    try:
        # Initialize display
        logger.debug("Initializing E-Ink display")
        epd = epd7in5_V2.EPD()
        
        # Initialize with timeout check
        init_timeout = time.time() + 30  # 30 second timeout
        epd.init()
        while epd.digital_read(epd.busy_pin) == 1:
            if time.time() > init_timeout:
                raise TimeoutError("Display initialization timed out")
            time.sleep(0.1)
        
        # Clear with timeout check
        logger.debug("Clearing display")
        clear_timeout = time.time() + 30
        epd.Clear()
        while epd.digital_read(epd.busy_pin) == 1:
            if time.time() > clear_timeout:
                raise TimeoutError("Display clear timed out")
            time.sleep(0.1)
        
        # Create canvas
        image = Image.new('1', (epd.width, epd.height), 255)
        draw = ImageDraw.Draw(image)
        
        # Set up fonts with fallback
        try:
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
            small_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
        except Exception as e:
            logger.warning(f"Font loading failed: {str(e)}, using default font")
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Extract and format aircraft data
        flight = aircraft_data.get('flight', 'N/A').strip()
        aircraft_type = aircraft_data.get('t', 'N/A')
        altitude = aircraft_data.get('alt_baro', 'N/A')
        speed = aircraft_data.get('gs', 'N/A')
        registration = aircraft_data.get('r', 'N/A')
        distance = aircraft_data.get('dst', 'N/A')
        
        text_lines = [
            f"Flight: {flight}",
            f"Registration: {registration}",
            f"Aircraft Type: {aircraft_type}",
            f"Altitude: {altitude} ft",
            f"Ground Speed: {speed} knots",
            f"Distance: {distance} NM"
        ]

        # Draw text
        y_position = 30
        for line in text_lines:
            draw.text((30, y_position), line, font=font, fill=0)
            y_position += 40

        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draw.text((30, y_position + 20), f"Last Updated: {timestamp}", font=small_font, fill=0)

        # Update display with timeout
        logger.debug("Updating display with new image")
        display_timeout = time.time() + 30
        epd.display(epd.getbuffer(image))
        while epd.digital_read(epd.busy_pin) == 1:
            if time.time() > display_timeout:
                raise TimeoutError("Display update timed out")
            time.sleep(0.1)
        
        logger.debug("Display update completed successfully")
        
    except Exception as e:
        logger.error(f"Display update failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        if epd is not None:
            logger.debug("Putting display to sleep")
            try:
                epd.sleep()
            except Exception as e:
                logger.error(f"Error putting display to sleep: {str(e)}")

def wait_for_display_ready(epd, timeout_seconds=10):
    """Helper function to wait for display to be ready with timeout"""
    timeout = time.time() + timeout_seconds
    while epd.digital_read(epd.busy_pin) == 1:
        if time.time() > timeout:
            raise TimeoutError(f"Display busy timeout after {timeout_seconds} seconds")
        time.sleep(0.1)

# Main Execution
#----------------------------------------
logger.info("Starting main execution loop")
try:
    while True:
        logger.debug("Starting new update cycle")
        # closest_aircraft = get_closest_aircraft() // This works.
        # Use mock data for testing
        closest_aircraft = {
            'flight': 'TEST123',
            'r': 'N12345',
            't': 'B738',
            'alt_baro': 35000,
            'gs': 450,
            'dst': 12.5
        }
        if closest_aircraft:
            logger.debug("Retrieved aircraft data, updating display")
            update_display(closest_aircraft)
        else:
            logger.warning("No aircraft data received")
        logger.debug("Waiting 30 seconds before next update")
        time.sleep(30)
except KeyboardInterrupt:
    logger.info("Program terminated by user")
except Exception as e:
    logger.error(f"Main loop error: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
finally:
    logger.debug("Cleaning up GPIO")
    GPIO.cleanup()