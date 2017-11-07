import display

width, height = 320, 240
verify_height = 40
speed = 4
trapezoid_top_width = 10
top_anchor = range(width / 2 - trapezoid_top_width * 2,
                   width / 2 + trapezoid_top_width * 2 + 1,
                   trapezoid_top_width)
bottom_anchor = range(0, width + 1, width / 4)


class Trapezoid(object):
    def __init__(self, screen, top, bottom, index, left_slope, right_slope, color):
        self.screen = screen
        self.top = top
        self.bottom = bottom
        self.index = index
        self.left_slope = left_slope
        self.right_slope = right_slope
        self.color = color

    def get_points(self):
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
        self.screen.render_polygon(self.get_points(), color and color or self.color)
        return self

    def move_down(self):
        self.top = min(height, self.top + speed)
        self.bottom = min(height, self.bottom + speed)
        return self.top < height - verify_height


class Note(object):
    def __init__(self, screen, index, color):
        self.color = color
        self.left_slope = (top_anchor[index] != bottom_anchor[index]
                           and (height / float(bottom_anchor[index] - top_anchor[index]), )
                           or (0, ))[0]
        self.right_slope = (top_anchor[index+1] != bottom_anchor[index+1]
                            and (height / float(bottom_anchor[index+1] - top_anchor[index+1]),)
                            or (0, ))[0]
        self.trapezoids = []
        self.verify = Trapezoid(screen, height - verify_height, height, index,
                                self.left_slope, self.right_slope, self.color)

    def move_all_trapezoids(self, pressed):
        self.verify.render(pressed and self.trapezoids and self.trapezoids[0].bottom >= height - verify_height
                           and self.color or display.PINK)
        self.trapezoids = [trapezoid.render() for trapezoid in self.trapezoids if trapezoid.move_down()]


class Visualizer(object):
    def __init__(self, on_tft=False):
        self.screen = display.Screen(width, height, on_tft)
        self.notes = [Note(self.screen, 0, display.WHITE),
                      Note(self.screen, 1, display.RED),
                      Note(self.screen, 2, display.GREEN),
                      Note(self.screen, 3, display.BLUE)]

    def refresh(self, frame, pressed):
        self.screen.clear()
        for pos in self.screen.get_click_pos():
            print pos
            exit(0)

        for i in range(4):
            if frame[i]:
                if len(self.notes[i].trapezoids) and self.notes[i].trapezoids[-1].top == height:
                    self.notes[i].trapezoids[-1].top -= speed
                else:
                    self.notes[i].trapezoids.append(Trapezoid(self.screen, -speed, 0, i,
                                                              self.notes[i].left_slope,
                                                              self.notes[i].right_slope,
                                                              self.notes[i].color))
            self.notes[i].move_all_trapezoids(pressed[i])

        self.screen.display()

    def tick(self):
        self.screen.tick(60)


if __name__ == "__main__":
    visualizer = Visualizer()

    try:
        with open("music.map", "rb") as fp:
            for byte in fp.read():
                visualizer.refresh([ord(byte) >> 3 & 0x1,
                                    ord(byte) >> 2 & 0x1,
                                    ord(byte) >> 1 & 0x1,
                                    ord(byte) >> 0 & 0x1], [1]*4)
                visualizer.tick()

    except KeyboardInterrupt:
        pass
