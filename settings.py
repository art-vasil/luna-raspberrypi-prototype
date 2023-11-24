import os

CUR_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(CUR_DIR, 'config.cfg')
ROAD_MODEL_PATH = os.path.join(CUR_DIR, 'utils', 'model', 'road-segmentation-adas-0001.blob')

# ------------------------------------- Battery Settings -----------------------------------------------------------
MAX_BATTERY = 4.05
MIN_BATTERY = 3.75

MIN_FRACTION = 0.075
SAFE_FRACTION = 0.25
MIDDLE_FRACTION = 0.15
DANGER_FRACTION = 0.10

LED_INTERVAL = 30
BLINK_INTERVAL = 1.0
FAST_INTERVAL = 0.5
GREEN_INTERVAL = 0
SHUTDOWN_INTERVAL = 30

RED_PIN = 21
GREEN_PIN = 20
ADC_PIN = 0
ADC_MAX = 2048
ADC_VOL = 4.096
ADC_GAIN = 1

FIRST_RESISTOR = 6800
SECOND_RESISTOR = 10000
# -----------------------------------------------------------------------------------------------------------------

# --------------------------------- Road Segmentation -------------------------------------------------------------
NN_WIDTH = 896
NN_HEIGHT = 512

CLASSES_COLOR_MAP = [
            (0, 0, 0),  # sky
            (58, 169, 55),  # road
            (211, 51, 17),
            (157, 80, 44)
        ]
CAM_OPTIONS = ['rgb', 'left', 'right']
# -----------------------------------------------------------------------------------------------------------------

# ------------------------------- SenseHat Settings ---------------------------------------------------------------
FRAME_HEIGHT = 8  # Height of display
FRAME_WIDTH = 8  # Width of display

# Colors in use
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 150, 0)
ORANGE = (255, 100, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
# ----------------------------------------------------------------------------------------------------------------

# ------------------------------- GPS Settings ---------------------------------------------------------------
GPS_POWER_KEY = 6
# ----------------------------------------------------------------------------------------------------------------

ALLOWED_ACTIONS = ['both', 'publish', 'subscribe']
