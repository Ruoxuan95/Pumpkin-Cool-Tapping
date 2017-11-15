import RPi.GPIO as GPIO


def key_initiate(all_pin):
    GPIO.setmode(GPIO.BCM)
    [GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) for pin in all_pin]

       
def key_status(all_pin):
    return [not GPIO.input(pin) for pin in all_pin]


def key_clean():
    GPIO.cleanup()


def parse_record(file_path):
    with open(file_path, "rb") as fp:
        for byte in fp.read():
            yield 0x1 << int(byte)
