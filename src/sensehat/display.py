import numpy as np
import math

from sense_hat import SenseHat
from settings import FRAME_WIDTH, FRAME_HEIGHT, BLACK, RED, ORANGE, GREEN, BLUE, WHITE, YELLOW


class RpiSenseHat:
    def __init__(self):
        self.sense = SenseHat()
        self.sense.low_light = True  # Display brightness
        self.sense.set_rotation(0)  # Screen rotation
        self.sense.clear()
        # Frame buffer of FRAME_HEIGHT x FRAME_WIDTH x RGB
        self._frame_buffer = np.full((FRAME_HEIGHT, FRAME_WIDTH), BLACK, dtype=(np.uint, 3))
        self.pages = [
            self.render_main,
            self.render_temperature,
            self.render_humidity,
            self.render_gyroscope,
            self.render_accelerometer,
            self.render_shutdown
        ]

    @staticmethod
    def _log(s):
        # Print on same line. Use equal width so
        # previously printed data is overwritten.
        # Mind the max width.
        print(' {0:80}'.format(s), end='\r')

    def _clear_frame_buffer(self):
        for idx in np.ndindex(self._frame_buffer.shape[:2]):  # 8x8x3, use 8x8
            self._frame_buffer[idx] = BLACK

    def _render_frame_buffer(self):
        self.sense.set_pixels(self._frame_buffer.reshape((64, 3)))

    def start(self):
        page_index = 0
        total_pages = len(self.pages)
        while True:
            for event in self.sense.stick.get_events():
                # Check if the joystick was pressed.
                if event.action == "released":
                    # Check which direction.
                    if event.direction == "up":
                        page_index = (page_index - 1) % total_pages
                    elif event.direction == "down":
                        page_index = (page_index + 1) % total_pages
                    elif event.direction == "left":
                        self.sense.show_letter("L")      # Left arrow
                    elif event.direction == "right":
                        self.sense.show_letter("R")      # Right arrow
                    elif event.direction == "middle":
                        self.sense.show_letter("M")      # Enter key

            self.pages[page_index]()

    def render_main(self):
        self._clear_frame_buffer()

        # Status indicators.
        self._frame_buffer[0:2, 0:2] = np.full(2, RED, dtype=(np.uint, 3))
        self._frame_buffer[0:2, 3:5] = np.full(2, ORANGE, dtype=(np.uint, 3))
        self._frame_buffer[0:2, 6:8] = np.full(2, GREEN, dtype=(np.uint, 3))

        # On-road/off-road indication.
        self._frame_buffer[3:, 0] = np.full(5, GREEN, dtype=(np.uint, 3))
        self._frame_buffer[3:, 7] = np.full(5, GREEN, dtype=(np.uint, 3))

        # Render pedestrian count (ex 5 here).
        self._frame_buffer[3, 2:6] = np.full(4, BLUE, dtype=(np.uint, 3))
        self._frame_buffer[4, 2] = BLUE
        self._frame_buffer[5, 2:6] = np.full(4, BLUE, dtype=(np.uint, 3))
        self._frame_buffer[6, 5] = BLUE
        self._frame_buffer[7, 2:6] = np.full(4, BLUE, dtype=(np.uint, 3))

        self._render_frame_buffer()
        self._log('Main page')

    def render_temperature(self):
        self._clear_frame_buffer()

        temperature = self.sense.get_temperature()

        # T °C
        self._frame_buffer[0, 0:3] = np.full(3, BLUE, dtype=(np.uint, 3))
        self._frame_buffer[0:3, 1] = np.full(3, BLUE, dtype=(np.uint, 3))

        self._frame_buffer[0, 4] = WHITE

        self._frame_buffer[0, 5:8] = np.full(3, BLUE, dtype=(np.uint, 3))
        self._frame_buffer[1, 5] = BLUE
        self._frame_buffer[2, 5:8] = np.full(3, BLUE, dtype=(np.uint, 3))

        # 38
        self._frame_buffer[3, 1:4] = np.full(3, ORANGE, dtype=(np.uint, 3))
        self._frame_buffer[3:, 3] = np.full(5, ORANGE, dtype=(np.uint, 3))
        self._frame_buffer[5, 1:4] = np.full(3, ORANGE, dtype=(np.uint, 3))
        self._frame_buffer[7, 1:4] = np.full(3, ORANGE, dtype=(np.uint, 3))

        self._frame_buffer[3, 6] = ORANGE
        self._frame_buffer[5, 6] = ORANGE
        self._frame_buffer[7, 6] = ORANGE
        self._frame_buffer[3:, 5] = np.full(5, ORANGE, dtype=(np.uint, 3))
        self._frame_buffer[3:, 7] = np.full(5, ORANGE, dtype=(np.uint, 3))

        self._render_frame_buffer()
        self._log(f'Temperature {temperature:.1f}°C')

    def render_humidity(self):
        self._clear_frame_buffer()
        humidity = self.sense.get_humidity()

        # H %
        self._frame_buffer[0:3, 0] = np.full(3, BLUE, dtype=(np.uint, 3))
        self._frame_buffer[1, 1] = BLUE
        self._frame_buffer[0:3, 2] = np.full(3, BLUE, dtype=(np.uint, 3))

        self._frame_buffer[0, 5] = WHITE
        self._frame_buffer[2, 7] = WHITE
        self._frame_buffer[0, 7] = BLUE
        self._frame_buffer[1, 6] = BLUE
        self._frame_buffer[2, 5] = BLUE

        # 30
        self._frame_buffer[3, 1:4] = np.full(3, YELLOW, dtype=(np.uint, 3))
        self._frame_buffer[3:, 3] = np.full(5, YELLOW, dtype=(np.uint, 3))
        self._frame_buffer[5, 1:4] = np.full(3, YELLOW, dtype=(np.uint, 3))
        self._frame_buffer[7, 1:4] = np.full(3, YELLOW, dtype=(np.uint, 3))

        self._frame_buffer[3, 6] = YELLOW
        self._frame_buffer[7, 6] = YELLOW
        self._frame_buffer[3:, 5] = np.full(5, YELLOW, dtype=(np.uint, 3))
        self._frame_buffer[3:, 7] = np.full(5, YELLOW, dtype=(np.uint, 3))

        self._render_frame_buffer()
        self._log(f'Humidity {humidity:.1f}%')

    def render_gyroscope(self):
        self._clear_frame_buffer()

        # x = y = 0
        # color = GREEN
        # pitch_level = roll_level = 0  # To categorize pitch/roll degrees.

        # get_orientation() returns degrees 0-360. For some reason, pitch is only showing 0-90 and 360-270 degrees,
        # so upside-down orientation cannot be determined by gyro pitch alone. For now, we manually convert to
        # degrees and consider only 0-(+/-90).
        # TODO: Investigate this further.
        # TODO: Investigate how to handle board orientation based on mounting.
        # Probably this will require using yaw as well.
        orientation = self.sense.get_orientation_radians()
        pitch = math.degrees(orientation["pitch"])  # -180 to +180
        roll = math.degrees(orientation["roll"])  # -180 to +180
        yaw = math.degrees(orientation["yaw"])  # -180 to +180

        self._log(s=f'Gyroscope pitch={pitch:.2f}, roll={roll:.2f}, yaw={yaw:.2f}')

        # Arbitrarily using 20 degree angle ranges to map to 8x8 LED matrix.
        # Left pitch
        if 0 <= pitch <= 20:
            pitch_level = 0
            x = 3
        elif 20 < pitch <= 40:
            pitch_level = 1
            x = 2
        elif 40 < pitch <= 60:
            pitch_level = 2
            x = 1
        elif pitch > 60:
            pitch_level = 3
            x = 0
        # Right pitch
        elif 0 > pitch >= -20:
            pitch_level = 0
            x = 4
        elif -20 > pitch >= -40:
            pitch_level = 1
            x = 5
        elif -40 > pitch >= -60:
            pitch_level = 2
            x = 6
        else:  # pitch <= -60:
            pitch_level = 3
            x = 7

        # Roll up
        if 0 <= roll <= 20:
            roll_level = 0
            y = 4
        elif 20 < roll <= 40:
            roll_level = 1
            y = 5
        elif 40 < roll <= 60:
            roll_level = 2
            y = 6
        elif roll > 60:
            roll_level = 3
            y = 7
        # Roll down
        elif 0 > roll >= -20:
            roll_level = 0
            y = 3
        elif -20 > roll >= -40:
            roll_level = 1
            y = 2
        elif -40 > roll >= -60:
            roll_level = 2
            y = 1
        else:  # roll <= -60:
            roll_level = 3
            y = 0

        level = max([pitch_level, roll_level])
        if level == 0:
            color = GREEN
        elif level == 1:
            color = YELLOW
        elif level == 2:
            color = ORANGE
        else:
            color = RED

        self._frame_buffer[y, x] = color
        self._render_frame_buffer()

    def render_accelerometer(self):
        self._clear_frame_buffer()

        # Draw a horizontal line with 2 pixel height as the baseline in the middle.
        self._frame_buffer[3:5] = np.full((2, FRAME_WIDTH), BLUE, dtype=(np.uint, 3))

        acceleration = self.sense.get_accelerometer_raw()
        x = acceleration['x']
        y = acceleration['y']
        z = acceleration['z']

        self._log(f'Accelerometer x={x:.2f}, y={y:.2f}, z={z:.2f}')

        for k, v in acceleration.items():
            a = round(v)
            # xp = 0
            if k == 'x':
                xp = 0
            elif k == 'y':
                xp = 3
            else:
                xp = 6

            # Round the acceleration and draw two column bar to reflect acceleration in x,y,z respectively.
            # Above the middle line is + and below -.
            if a >= 1:
                self._frame_buffer[2, xp:xp+2] = GREEN
                if a >= 2:
                    self._frame_buffer[1, xp:xp+2] = YELLOW
                if a >= 3:
                    self._frame_buffer[0, xp:xp+2] = RED
            elif a <= -1:
                self._frame_buffer[5, xp:xp+2] = GREEN
                if a <= -2:
                    self._frame_buffer[6, xp:xp+2] = YELLOW
                if a <= -3:
                    self._frame_buffer[7, xp:xp+2] = RED

        self._render_frame_buffer()

    def render_shutdown(self):
        self._clear_frame_buffer()

        # Power icon
        self._frame_buffer[1, 2] = RED
        self._frame_buffer[2, 1] = RED
        self._frame_buffer[3, 1] = RED
        self._frame_buffer[4, 1] = RED
        self._frame_buffer[5, 2] = RED
        self._frame_buffer[6, 3] = RED
        self._frame_buffer[6, 4] = RED
        self._frame_buffer[6, 5] = RED
        self._frame_buffer[5, 6] = RED
        self._frame_buffer[4, 7] = RED
        self._frame_buffer[3, 7] = RED
        self._frame_buffer[2, 7] = RED
        self._frame_buffer[1, 6] = RED
        self._frame_buffer[0:4, 4] = np.full(4, WHITE, dtype=(np.uint, 3))

        self._render_frame_buffer()
        self._log('Shutdown')

    def display_status(self, status):
        if status == "road":
            self.sense.clear((0, 255, 0))
        else:
            self.sense.clear((255, 0, 0))

        return


# Main
if __name__ == '__main__':
    senseHat = RpiSenseHat()
    senseHat.start()
