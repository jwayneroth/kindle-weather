import os
import logging
from dotenv import load_dotenv

LATITUDE = "40.74307"
LONGITUDE = "-73.9182"

RUN_ON_RASPBERRY_PI = os.uname()[4][:3] == 'arm'

HOME_DIR = os.path.expanduser("~")

IMG_DIRECTORY = os.path.dirname(__file__) + '/images/'
FONT_DIRECTORY = os.path.dirname(__file__) + '/fonts/'
DATA_DIRECTORY = os.path.dirname(__file__) + '/data/'

DISPLAY_WIDTH = 600
DISPLAY_HEIGHT = 800

formatter = logging.Formatter('%(asctime)s_%(levelname)s - %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)

fh = logging.FileHandler(DATA_DIRECTORY + 'pz_weather.log', 'a')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

logger = logging.getLogger('pz_weather_logger')
if RUN_ON_RASPBERRY_PI:
	logger.setLevel(logging.INFO)
else:
	logger.setLevel(logging.DEBUG)
logger.addHandler(ch)
logger.addHandler(fh)

load_dotenv()

OPEN_WEATHER_APP_ID = os.getenv("OPEN_WEATHER_APP_ID")

logger.debug("open weather api key {}".format(OPEN_WEATHER_APP_ID))