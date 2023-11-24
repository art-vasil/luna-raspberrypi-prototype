import os
import time
import Adafruit_ADS1x15
import RPi.GPIO as GPIO

from utils.folder_file_manager import log_print
from settings import CUR_DIR, MAX_BATTERY, MIN_BATTERY, MIN_FRACTION, SAFE_FRACTION, MIDDLE_FRACTION, DANGER_FRACTION, \
    LED_INTERVAL, BLINK_INTERVAL, FAST_INTERVAL, GREEN_INTERVAL, SHUTDOWN_INTERVAL, RED_PIN, GREEN_PIN, ADC_PIN, \
    ADC_MAX, ADC_VOL, ADC_GAIN, FIRST_RESISTOR, SECOND_RESISTOR


class BatteryMonitor:
    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        self.adc = Adafruit_ADS1x15.ADS1015()
        self.gain = ADC_GAIN
        self.battery_min_voltage = MIN_BATTERY
        self.battery_max_voltage = MAX_BATTERY
        self.fraction_battery_min = MIN_FRACTION
        self.poll_interval = LED_INTERVAL
        self.led_states = {'off': GPIO.LOW, 'on': GPIO.HIGH}
        self.led_pin = {'red': RED_PIN, 'green': GREEN_PIN}
        GPIO.setup(self.led_pin['red'], GPIO.OUT)
        GPIO.setup(self.led_pin['green'], GPIO.OUT)

    @staticmethod
    def voltage_divider(r1, r2, vin):
        v_real = vin * (r1 + r2) / r2
        return v_real

    @staticmethod
    def low_battery_shutdown():

        shutdown_delay = SHUTDOWN_INTERVAL  # seconds
        cmd = "sudo wall 'System shutting down in %d seconds'" % shutdown_delay
        os.system(cmd)
        time.sleep(shutdown_delay)
        # Log message is added to /var/log/messages
        os.system("sudo logger -t 'pi_power' '** Low Battery - shutting down now **'")
        GPIO.cleanup()
        os.system("sudo shutdown now")

    def green_constant(self):
        blink_time_on = GREEN_INTERVAL
        blink_time_off = GREEN_INTERVAL
        leds = ['green']
        self.update_leds(leds, blink_time_on, blink_time_off)

    def red_constant(self):
        blink_time_on = GREEN_INTERVAL
        blink_time_off = GREEN_INTERVAL
        leds = ['red']
        self.update_leds(leds, blink_time_on, blink_time_off)

    def red_blink(self):
        blink_time_on = BLINK_INTERVAL
        blink_time_off = BLINK_INTERVAL
        leds = ['red']
        self.update_leds(leds, blink_time_on, blink_time_off)

    def red_blink_fast(self):
        blink_time_on = FAST_INTERVAL
        blink_time_off = FAST_INTERVAL
        leds = ['red']
        self.update_leds(leds, blink_time_on, blink_time_off)

    def update_leds(self, current_leds, time_on, time_off):
        if time_off == 0:
            # constant on
            for i in range(len(current_leds)):
                GPIO.output(self.led_pin[current_leds[i]], self.led_states['on'])
            time.sleep(self.poll_interval)
        else:
            # blink
            n_cycles = int(float(self.poll_interval) / float(time_on + time_off))
            for i in range(n_cycles):
                # led on, sleep, led off, sleep
                for j in range(len(current_leds)):
                    GPIO.output(self.led_pin[current_leds[j]], self.led_states['on'])
                time.sleep(time_on)
                for j in range(len(current_leds)):
                    GPIO.output(self.led_pin[current_leds[j]], self.led_states['off'])
                time.sleep(time_off)

        return

    def run(self):
        st_time = time.time()
        GPIO.output(self.led_pin['red'], self.led_states['off'])
        GPIO.output(self.led_pin['green'], self.led_states['off'])
        while True:
            adc_value = self.adc.read_adc(ADC_PIN, gain=self.gain)
            adv_voltage = adc_value / ADC_MAX * ADC_VOL
            battery_voltage = self.voltage_divider(r1=FIRST_RESISTOR, r2=SECOND_RESISTOR, vin=adv_voltage)
            fraction_battery = (battery_voltage - self.battery_min_voltage) / (self.battery_max_voltage -
                                                                               self.battery_min_voltage)
            print(f"[INFO] AD Value: {adc_value}, Input Voltage: {adv_voltage}V, Battery Voltage: {battery_voltage}, "
                  f"Fraction: {fraction_battery}")
            log_print(info_str=f"[INFO] AD Value: {adc_value}, Input Voltage: {adv_voltage}V, "
                               f"Battery Voltage: {battery_voltage}, Fraction: {fraction_battery}",
                      file_path=os.path.join(CUR_DIR, "battery.log"))
            if fraction_battery < self.fraction_battery_min:
                print('[WARN] Low Battery - shutdown now')
                log_print(info_str=f'[WARN] Elapsed: {time.time() - st_time}, Low Battery: {battery_voltage} - '
                                   f'shutdown now',
                          file_path=os.path.join(CUR_DIR, "battery.log"))
                self.low_battery_shutdown()
            if fraction_battery >= SAFE_FRACTION:
                GPIO.output(self.led_pin["red"], self.led_states['off'])
                self.green_constant()
            elif MIDDLE_FRACTION <= fraction_battery <= SAFE_FRACTION:
                GPIO.output(self.led_pin["green"], self.led_states['off'])
                self.red_constant()
            elif DANGER_FRACTION <= fraction_battery <= MIDDLE_FRACTION:
                GPIO.output(self.led_pin["green"], self.led_states['off'])
                self.red_blink()
            else:
                GPIO.output(self.led_pin["green"], self.led_states['off'])
                self.red_blink_fast()


if __name__ == '__main__':
    BatteryMonitor().run()
