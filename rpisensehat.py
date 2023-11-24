from sense_hat import SenseHat
import numpy as np
import math


class RpiSenseHat:

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

    def __init__(self):
        self._senseHat = SenseHat()
        self._senseHat.low_light = True  # Display brightness
        self._senseHat.set_rotation(0)  # Screen rotation
        self._senseHat.clear()
        # Frame buffer of FRAME_HEIGHTxFRAME_WIDTHxRGB
        self._frame_buffer = np.full((self.FRAME_HEIGHT, self.FRAME_WIDTH), self.BLACK, dtype=(np.uint, 3))
        self.pages = [
            self.render_main,
            self.render_temperature,
            self.render_humidity,
            self.render_gyroscope,
            self.render_accelerometer,
            self.render_shutdown
        ]

    def _log(self, s):
        # Print on same line. Use equal width so
        # previously printed data is overwritten.
        # Mind the max width.
        print(' {0:80}'.format(s), end='\r')

    def _clear_frame_buffer(self):
        for idx in np.ndindex(self._frame_buffer.shape[:2]):  # 8x8x3, use 8x8
            self._frame_buffer[idx] = self.BLACK

    def _render_frame_buffer(self):
        self._senseHat.set_pixels(self._frame_buffer.reshape((64, 3)))

    def start(self):
        page_index = 0
        total_pages = len(self.pages)
        while True:
            for event in self._senseHat.stick.get_events():
                # Check if the joystick was pressed.
                if event.action == "released":
                    # Check which direction.
                    if event.direction == "up":
                        page_index = (page_index - 1) % total_pages
                    elif event.direction == "down":
                        page_index = (page_index + 1) % total_pages
                    elif event.direction == "left":
                        self._senseHat.show_letter("L")      # Left arrow
                    elif event.direction == "right":
                        self._senseHat.show_letter("R")      # Right arrow
                    elif event.direction == "middle":
                        self._senseHat.show_letter("M")      # Enter key

            self.pages[page_index]()

    def render_main(self):
        self._clear_frame_buffer()

        # Status indicators.
        self._frame_buffer[0:2, 0:2] = np.full(2, self.RED, dtype=(np.uint, 3))
        self._frame_buffer[0:2, 3:5] = np.full(2, self.ORANGE, dtype=(np.uint, 3))
        self._frame_buffer[0:2, 6:8] = np.full(2, self.GREEN, dtype=(np.uint, 3))

        # On-road/off-road indication.
        self._frame_buffer[3:, 0] = np.full(5, self.GREEN, dtype=(np.uint, 3))
        self._frame_buffer[3:, 7] = np.full(5, self.GREEN, dtype=(np.uint, 3))

        # Render pedestrian count (ex 5 here).
        self._frame_buffer[3, 2:6] = np.full(4, self.BLUE, dtype=(np.uint, 3))
        self._frame_buffer[4, 2] = self.BLUE
        self._frame_buffer[5, 2:6] = np.full(4, self.BLUE, dtype=(np.uint, 3))
        self._frame_buffer[6, 5] = self.BLUE
        self._frame_buffer[7, 2:6] = np.full(4, self.BLUE, dtype=(np.uint, 3))

        self._render_frame_buffer()
        self._log('Main page')

    def render_temperature(self):
        self._clear_frame_buffer()

        temperature = self._senseHat.get_temperature()

        # T °C
        self._frame_buffer[0, 0:3] = np.full(3, self.BLUE, dtype=(np.uint, 3))
        self._frame_buffer[0:3, 1] = np.full(3, self.BLUE, dtype=(np.uint, 3))

        self._frame_buffer[0, 4] = self.WHITE

        self._frame_buffer[0, 5:8] = np.full(3, self.BLUE, dtype=(np.uint, 3))
        self._frame_buffer[1, 5] = self.BLUE
        self._frame_buffer[2, 5:8] = np.full(3, self.BLUE, dtype=(np.uint, 3))

        # 38
        self._frame_buffer[3, 1:4] = np.full(3, self.ORANGE, dtype=(np.uint, 3))
        self._frame_buffer[3:, 3] = np.full(5, self.ORANGE, dtype=(np.uint, 3))
        self._frame_buffer[5, 1:4] = np.full(3, self.ORANGE, dtype=(np.uint, 3))
        self._frame_buffer[7, 1:4] = np.full(3, self.ORANGE, dtype=(np.uint, 3))

        self._frame_buffer[3, 6] = self.ORANGE
        self._frame_buffer[5, 6] = self.ORANGE
        self._frame_buffer[7, 6] = self.ORANGE
        self._frame_buffer[3:, 5] = np.full(5, self.ORANGE, dtype=(np.uint, 3))
        self._frame_buffer[3:, 7] = np.full(5, self.ORANGE, dtype=(np.uint, 3))

        self._render_frame_buffer()
        self._log(f'Temperature {temperature:.1f}°C')

    def render_humidity(self):
        self._clear_frame_buffer()

        humidity = self._senseHat.get_humidity()

        # H %
        self._frame_buffer[0:3, 0] = np.full(3, self.BLUE, dtype=(np.uint, 3))
        self._frame_buffer[1, 1] = self.BLUE
        self._frame_buffer[0:3, 2] = np.full(3, self.BLUE, dtype=(np.uint, 3))

        self._frame_buffer[0, 5] = self.WHITE
        self._frame_buffer[2, 7] = self.WHITE
        self._frame_buffer[0, 7] = self.BLUE
        self._frame_buffer[1, 6] = self.BLUE
        self._frame_buffer[2, 5] = self.BLUE

        # 30
        self._frame_buffer[3, 1:4] = np.full(3, self.YELLOW, dtype=(np.uint, 3))
        self._frame_buffer[3:, 3] = np.full(5, self.YELLOW, dtype=(np.uint, 3))
        self._frame_buffer[5, 1:4] = np.full(3, self.YELLOW, dtype=(np.uint, 3))
        self._frame_buffer[7, 1:4] = np.full(3, self.YELLOW, dtype=(np.uint, 3))

        self._frame_buffer[3, 6] = self.YELLOW
        self._frame_buffer[7, 6] = self.YELLOW
        self._frame_buffer[3:, 5] = np.full(5, self.YELLOW, dtype=(np.uint, 3))
        self._frame_buffer[3:, 7] = np.full(5, self.YELLOW, dtype=(np.uint, 3))

        self._render_frame_buffer()
        self._log(f'Humidity {humidity:.1f}%')

    def render_gyroscope(self):
        self._clear_frame_buffer()

        x = y = 0
        color = self.GREEN
        pitch_level = roll_level = 0  # To categorize pitch/roll degrees.

        # get_orientation() returns degrees 0-360.
        # For some reason, pitch is only
        # showing 0-90 and 360-270 degrees, so upside-down
        # orientation cannot be determined by gyro pitch alone.
        # For now, we manually convert to degrees and consider
        # only 0-(+/-90).
        # TODO: Investigate this further.
        # TODO: Investigate how to handle board orientation based on mounting.
        #       Probably this will require using yaw as well.
        orientation = self._senseHat.get_orientation_radians()
        pitch = math.degrees(orientation["pitch"])  # -180 to +180
        roll = math.degrees(orientation["roll"])  # -180 to +180
        yaw = math.degrees(orientation["yaw"])  # -180 to +180

        self._log(f'Gyroscope pitch={pitch:.2f}, roll={roll:.2f}, yaw={yaw:.2f}')

        # Arbitrarily using 20 degree angle ranges to map to 8x8 LED matrix.
        # Left pitch
        if pitch >= 0 and pitch <= 20:
            pitch_level = 0
            x = 3
        elif pitch > 20 and pitch <= 40:
            pitch_level = 1
            x = 2
        elif pitch > 40 and pitch <= 60:
            pitch_level = 2
            x = 1
        elif pitch > 60:
            pitch_level = 3
            x = 0
        # Right pitch
        elif pitch < 0 and pitch >= -20:
            pitch_level = 0
            x = 4
        elif pitch < -20 and pitch >= -40:
            pitch_level = 1
            x = 5
        elif pitch < -40 and pitch >= -60:
            pitch_level = 2
            x = 6
        else:  # pitch <= -60:
            pitch_level = 3
            x = 7

        # Roll up
        if roll >= 0 and roll <= 20:
            roll_level = 0
            y = 4
        elif roll > 20 and roll <= 40:
            roll_level = 1
            y = 5
        elif roll > 40 and roll <= 60:
            roll_level = 2
            y = 6
        elif roll > 60:
            roll_level = 3
            y = 7
        # Roll down
        elif roll < 0 and roll >= -20:
            roll_level = 0
            y = 3
        elif roll < -20 and roll >= -40:
            roll_level = 1
            y = 2
        elif roll < -40 and roll >= -60:
            roll_level = 2
            y = 1
        else:  # roll <= -60:
            roll_level = 3
            y = 0

        level = max([pitch_level, roll_level])
        if level == 0:
            color = self.GREEN
        elif level == 1:
            color = self.YELLOW
        elif level == 2:
            color = self.ORANGE
        else:
            color = self.RED

        self._frame_buffer[y, x] = color
        self._render_frame_buffer()

    def render_accelerometer(self):
        self._clear_frame_buffer()

        # Draw a horizontal line with 2 pixel height as the baseline in the middle.
        self._frame_buffer[3:5] = np.full((2, self.FRAME_WIDTH), self.BLUE, dtype=(np.uint, 3))

        acceleration = self._senseHat.get_accelerometer_raw()
        x = acceleration['x']
        y = acceleration['y']
        z = acceleration['z']

        self._log(f'Accelerometer x={x:.2f}, y={y:.2f}, z={z:.2f}')

        for k, v in acceleration.items():
            a = round(v)
            xp = 0
            if k == 'x':
                xp = 0
            elif k == 'y':
                xp = 3
            else:
                xp = 6

            # Round the acceleration and draw two column bar
            # to reflect acceleration in x,y,z respectively.
            # Above the middle line is + and below -.
            if a >= 1:
                self._frame_buffer[2, xp:xp+2] = self.GREEN
                if a >= 2:
                    self._frame_buffer[1, xp:xp+2] = self.YELLOW
                if a >= 3:
                    self._frame_buffer[0, xp:xp+2] = self.RED
            elif a <= -1:
                self._frame_buffer[5, xp:xp+2] = self.GREEN
                if a <= -2:
                    self._frame_buffer[6, xp:xp+2] = self.YELLOW
                if a <= -3:
                    self._frame_buffer[7, xp:xp+2] = self.RED

        self._render_frame_buffer()

    def render_shutdown(self):
        self._clear_frame_buffer()

        # Power icon
        self._frame_buffer[1, 2] = self.RED
        self._frame_buffer[2, 1] = self.RED
        self._frame_buffer[3, 1] = self.RED
        self._frame_buffer[4, 1] = self.RED
        self._frame_buffer[5, 2] = self.RED
        self._frame_buffer[6, 3] = self.RED
        self._frame_buffer[6, 4] = self.RED
        self._frame_buffer[6, 5] = self.RED
        self._frame_buffer[5, 6] = self.RED
        self._frame_buffer[4, 7] = self.RED
        self._frame_buffer[3, 7] = self.RED
        self._frame_buffer[2, 7] = self.RED
        self._frame_buffer[1, 6] = self.RED

        self._frame_buffer[0:4, 4] = np.full(4, self.WHITE, dtype=(np.uint, 3))

        self._render_frame_buffer()
        self._log('Shutdown')


# Main
if __name__ == '__main__':
    senseHat = RpiSenseHat()
    senseHat.start()
