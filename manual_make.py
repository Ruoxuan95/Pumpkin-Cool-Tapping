import time
import RPi.GPIO as GPIO
import keyboard


dict_pin = {17: "1", 22: "2", 23: "3", 27: "4"}
all_pin = [17, 22, 23, 27]
keyboard.key_initiate(all_pin)


txt = ""


running = True
while running:
    try:
        time.sleep(1.0/30)
        old_length = len(txt)
        for pin, number in dict_pin.items():
            if not GPIO.input(pin):
                txt += number
                break
        if len(txt) == old_length:
            txt += "0"
        if len(txt) == 8:
            with open("record.txt", "ab") as fp:
                fp.write(txt)
            txt = ""
    except KeyboardInterrupt:
            running = False

GPIO.cleanup()

