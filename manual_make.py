import time
import RPi.GPIO as GPIO
import keyboard


dict_pin = {19: "1", 13: "2", 23: "3", 26: "4"}
all_pin = [19, 13, 23, 26]
keyboard.key_initiate(all_pin)


txt = ""


running = True
while running:
    try:
        time.sleep(1.0/30)
        txt += "0"
        for pin, number in dict_pin.items():
            if not GPIO.input(pin):
                txt += number
        if len(txt) == 8:
            with open("record.txt", "wb+") as fp:
                fp.write(txt)
            txt = ""
    except KeyboardInterrupt:
            running = False

GPIO.cleanup()

