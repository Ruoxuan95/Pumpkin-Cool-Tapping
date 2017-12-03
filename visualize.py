import display
import keyboard
from time import time, sleep
import numpy as np
import subprocess


verify_height = 40
trapezoid_top_width = 10
top_anchor = range(display.width / 2 - trapezoid_top_width * 2,
                   display.width / 2 + trapezoid_top_width * 2 + 1,
                   trapezoid_top_width)
bottom_anchor = range(0, display.width + 1, display.width / 4)
select_pos = [(160, 30), (160, 90), (160, 150), (160, 210)]


class Trapezoid(object):
    def __init__(self, screen, top, bottom, index, left_slope, right_slope, color, speed):
        self.screen = screen
        self.top = top
        self.bottom = bottom
        self.index = index
        self.left_slope = left_slope
        self.right_slope = right_slope
        self.color = color
        self.speed = speed

    def _get_points(self):
        return [[(self.left_slope
                  and (self.top / self.left_slope + top_anchor[self.index],)
                  or (top_anchor[self.index],))[0], self.top],

                [(self.right_slope
                  and (self.top / self.right_slope + top_anchor[self.index + 1],)
                  or (top_anchor[self.index + 1],))[0], self.top],

                [(self.right_slope
                  and (self.bottom / self.right_slope + top_anchor[self.index + 1],)
                  or (top_anchor[self.index + 1],))[0], self.bottom],

                [(self.left_slope
                  and (self.bottom / self.left_slope + top_anchor[self.index],)
                  or (top_anchor[self.index],))[0], self.bottom]]

    def render(self, color=None):
        self.screen.render_polygon(self._get_points(), color and color or self.color)
        return self

    def move_down(self):
        self.top = min(display.height, self.top + self.speed)
        self.bottom = min(display.height - verify_height, self.bottom + self.speed)
        return self.top < display.height - verify_height


class Note(object):
    def __init__(self, screen, index, color, speed):
        self.color = color
        self.left_slope = (top_anchor[index] != bottom_anchor[index]
                           and (display.height / float(bottom_anchor[index] - top_anchor[index]),)
                           or (0,))[0]
        self.right_slope = (top_anchor[index + 1] != bottom_anchor[index + 1]
                            and (display.height / float(bottom_anchor[index + 1] - top_anchor[index + 1]),)
                            or (0,))[0]
        self.trapezoids = []
        self.verify = Trapezoid(screen, display.height - verify_height, display.height, index,
                                self.left_slope, self.right_slope, self.color, speed)

    def move_all_trapezoids(self, pressed):
        self.trapezoids = [trapezoid.render() for trapezoid in self.trapezoids if trapezoid.move_down()]
        self.verify.render(pressed and self.trapezoids and self.trapezoids[0].bottom >= display.height - verify_height
                           and self.color or display.PINK)


class Visualizer(object):
    def __init__(self, music_path="", fifo="", trapezoid_height=20, speed=2, on_tft=False, screen=None):
        self.screen = screen and screen or display.Screen(on_tft=on_tft)
        self.screen.clear()
        self.screen.render_text({"Loading...": (160, 120)}, 40, display.WHITE)
        self.screen.display()
        self.cross_screen = (display.height - verify_height) / speed
        self.notes = [Note(self.screen, 0, display.WHITE, speed),
                      Note(self.screen, 1, display.RED, speed),
                      Note(self.screen, 2, display.GREEN, speed),
                      Note(self.screen, 3, display.BLUE, speed)]
        self.trapezoid_height = trapezoid_height
        self.state = [0, 0, 0, 0]
        self.speed = speed
        if music_path and fifo:
            self.fifo = fifo
            subprocess.call(["mplayer -input file={} {} &".format(fifo, music_path)], shell=True)
            subprocess.check_output("echo 'pause' > {}".format(fifo), shell=True)

    def play_music(self):
        subprocess.check_output("echo 'pause' > {}".format(self.fifo), shell=True)

    def stop_music(self):
        subprocess.check_output("echo 'quit' > {}".format(self.fifo), shell=True)

    def map_file_refresh(self, frame, pressed):
        self.screen.clear()

        for i in range(4):
            if frame >> 3 - i & 0x01:
                if len(self.notes[i].trapezoids) and self.notes[i].trapezoids[-1].top == display.height:
                    self.notes[i].trapezoids[-1].top -= self.speed
                else:
                    self.notes[i].trapezoids.append(Trapezoid(self.screen, -self.speed, 0, i,
                                                              self.notes[i].left_slope,
                                                              self.notes[i].right_slope,
                                                              self.notes[i].color, self.speed))
            self.notes[i].move_all_trapezoids(pressed[i])

        self.screen.display()

        for pos in self.screen.get_click_pos():
            print pos
            return False

        return True

    def detection_refresh(self, frame, pressed):
        self.screen.clear()

        new_state = [0] * 4
        for i in range(4):
            if frame[i]:
                # set state value to designated height for countdown
                new_state[i] = self.trapezoid_height

                if self.state[i]:
                    self.notes[i].trapezoids[-1].top -= self.speed
                else:
                    self.notes[i].trapezoids.append(Trapezoid(self.screen, -self.speed, 0, i,
                                                              self.notes[i].left_slope,
                                                              self.notes[i].right_slope,
                                                              self.notes[i].color, self.speed))
            elif self.state[i]:
                self.notes[i].trapezoids[-1].top -= self.speed
                new_state[i] = self.state[i] - 1

            self.notes[i].move_all_trapezoids(pressed[i])

        self.state = new_state
        self.screen.display()

        for pos in self.screen.get_click_pos():
            print pos
            return True

        return False


class MapReader(object):
    def __init__(self, music_path, map_path, pin_list, frame_rate, speed=2, on_tft=False, screen=None):
        self.record = np.load(map_path)
        self.pin_list = pin_list
        keyboard.key_initiate(pin_list)
        self.interval = 1.0 / frame_rate
        self.visualizer = Visualizer(music_path, "mplayer_fifo", 0, speed, on_tft, screen)

    def __call__(self):
        timestamp = time()
        display_start = time()
        counter = 0

        try:
            for idx in range(len(self.record)):
                counter += 1
                if counter == self.visualizer.cross_screen:
                    self.visualizer.play_music()

                if not self.visualizer.map_file_refresh(self.record[idx], keyboard.key_status(self.pin_list)):
                    break

                sleep_time = timestamp + self.interval - time()
                if sleep_time > 0:
                    sleep(sleep_time)
                timestamp += self.interval

        except KeyboardInterrupt:
            pass

        finally:
            self.visualizer.stop_music()
            keyboard.key_clean()
            print("Elapsed time: {:.2f}s".format(time() - display_start))


if __name__ == "__main__":
    map_reader = MapReader("peace.mp3", "peace&love.npy", [26, 13, 6, 5], 60)
    map_reader()
