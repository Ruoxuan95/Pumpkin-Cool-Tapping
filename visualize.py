import display
import keyboard


width, height = 320, 240
verify_height = 40
trapezoid_top_width = 10
top_anchor = range(width / 2 - trapezoid_top_width * 2,
                   width / 2 + trapezoid_top_width * 2 + 1,
                   trapezoid_top_width)
bottom_anchor = range(0, width + 1, width / 4)


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
                  and (self.top / self.left_slope + top_anchor[self.index], )
                  or (top_anchor[self.index], ))[0], self.top],

                [(self.right_slope
                  and (self.top / self.right_slope + top_anchor[self.index+1], )
                  or (top_anchor[self.index+1], ))[0], self.top],

                [(self.right_slope
                  and (self.bottom / self.right_slope + top_anchor[self.index+1], )
                  or (top_anchor[self.index+1], ))[0], self.bottom],

                [(self.left_slope
                  and (self.bottom / self.left_slope + top_anchor[self.index], )
                  or (top_anchor[self.index], ))[0], self.bottom]]

    def render(self, color=None):
        self.screen.render_polygon(self._get_points(), color and color or self.color)
        return self

    def move_down(self):
        self.top = min(height, self.top + self.speed)
        self.bottom = min(height - verify_height, self.bottom + self.speed)
        return self.top < height - verify_height


class Note(object):
    def __init__(self, screen, index, color, speed):
        self.color = color
        self.left_slope = (top_anchor[index] != bottom_anchor[index]
                           and (height / float(bottom_anchor[index] - top_anchor[index]), )
                           or (0, ))[0]
        self.right_slope = (top_anchor[index+1] != bottom_anchor[index+1]
                            and (height / float(bottom_anchor[index+1] - top_anchor[index+1]),)
                            or (0, ))[0]
        self.trapezoids = []
        self.verify = Trapezoid(screen, height - verify_height, height, index,
                                self.left_slope, self.right_slope, self.color, speed)

    def move_all_trapezoids(self, pressed):
        self.trapezoids = [trapezoid.render() for trapezoid in self.trapezoids if trapezoid.move_down()]
        self.verify.render(pressed and self.trapezoids and self.trapezoids[0].bottom >= height - verify_height
                           and self.color or display.PINK)


class Visualizer(object):
    def __init__(self, speed=1, on_tft=False):
        self.screen = display.Screen(width, height, on_tft)
        self.notes = [Note(self.screen, 0, display.WHITE, speed),
                      Note(self.screen, 1, display.RED, speed),
                      Note(self.screen, 2, display.GREEN, speed),
                      Note(self.screen, 3, display.BLUE, speed)]
        self.state = [0, 0, 0, 0]
        self.speed = speed

    def refresh_map_file(self, frame, pressed):
        self.screen.clear()

        for i in range(4):
            if frame >> 4-i & 0x01:
                if len(self.notes[i].trapezoids) and self.notes[i].trapezoids[-1].top == height:
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

    def real_time_refresh(self, current_frame, future_frame, pressed):
        self.screen.clear()

        new_state = [0] * 4
        for i in range(4):
            if current_frame[i]:
                if self.state[i]:
                    self.notes[i].trapezoids[-1].top -= self.speed
                    new_state[i] = 1
                elif future_frame[i]:
                    self.notes[i].trapezoids.append(Trapezoid(self.screen, -self.speed, 0, i,
                                                              self.notes[i].left_slope,
                                                              self.notes[i].right_slope,
                                                              self.notes[i].color, self.speed))
                    new_state[i] = 1
            self.notes[i].move_all_trapezoids(pressed[i])
        self.state = new_state

        self.screen.display()

        for pos in self.screen.get_click_pos():
            print pos
            return False

        return True


if __name__ == "__main__":
    visualizer = Visualizer(2, True)
    all_pin = [17, 22, 23, 27]

    try:
        keyboard.key_initiate(all_pin)
        for byte in keyboard.parse_record("record.txt"):
            if not visualizer.refresh_map_file(int(byte), keyboard.key_status(all_pin)):
                break
            visualizer.screen.tick(42)

    except KeyboardInterrupt:
        pass
