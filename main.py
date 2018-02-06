import display
from visualize import select_pos, MapReader
from analyze import Analyzer
from time import sleep


select_text = ["Easy - Peace & Love", "Medium - Locked Away", "Hard - July", "QUIT"]
select_music = {k: v for (k, v) in zip(select_text, select_pos)}
screen = display.Screen(on_tft=True)
all_pin = [5, 6, 13, 26][::-1]
frame_rate = 60
response_time = 0.1


def display_select_music():
    screen.clear()
    screen.render_text(select_music, 40, display.WHITE)
    screen.display()


display_select_music()
running = True
while running:
    pos = screen.get_click_pos()
    if pos:
        if pos[0][1] > 180:
            running = False
        else:
            if pos[0][1] < 60:
                MapReader("peace.mp3", "peace&love.npy", all_pin, frame_rate, screen=screen)()
            elif pos[0][1] < 120:
                Analyzer("locked.mp3", 44100, frame_rate, 0, all_pin, response_time, screen=screen)()
            else:
                Analyzer("july.mp3", 44100, frame_rate, 0, all_pin, response_time, screen=screen)()
            display_select_music()

    sleep(0.05)
