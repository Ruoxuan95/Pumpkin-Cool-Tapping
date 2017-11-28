import RPi.GPIO as GPIO
import keyboard
import pygame
from time import time, sleep
import numpy as np

dict_pin = {5: 8, 6: 4, 13: 2, 26: 1}
all_pin = [5, 6, 13, 26]
keyboard.key_initiate(all_pin)

pygame.mixer.init()
pygame.mixer.music.load("AWA.mp3")
pygame.mixer.music.play()

record = []
timestamp = time()
running = True
while running:
    try:
        current = 0
        for pin, number in dict_pin.items():
            if not GPIO.input(pin):
                current += number
        record.append(current)

        while time() - timestamp < 1.0 / 60:
            sleep(0.000001)
        timestamp += 1.0 / 60

    except KeyboardInterrupt:
        running = False
        np.save("record", np.array(record))

GPIO.cleanup()
