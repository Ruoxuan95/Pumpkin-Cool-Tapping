import RPi.GPIO as GPIO


def key_initiate(all_pin):
    GPIO.setmode(GPIO.BCM)
    [GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) for pin in all_pin]

       
def key_status(all_pin):
    return [not GPIO.input(pin) for pin in all_pin]


def key_clean():
    GPIO.cleanup()

def parse_record():
    with open("record.txt", "rb") as fp:
        map_record = []
        for byte in fp.read():

            if int(byte) == 0:
                map_record = [0, 0, 0, 0]
            if int(byte) == 1:
                map_record = [1, 0, 0, 0]
            if int(byte) == 2:
                map_record = [0, 1, 0, 0]
            if int(byte) == 3:
                map_record = [0, 0, 1, 0]
            if int(byte) == 4:
                map_record = [0, 0, 0, 1]

            yield map_record