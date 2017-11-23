import numpy as np
from scipy.io.wavfile import read
from visualize import Visualizer
import keyboard
import threading
import Queue


class Data(object):
    def __init__(self, data_chunks, chunk_size):
        self.position = 0
        self.data = data_chunks
        self.chunk_size = chunk_size

    def next_chunk(self):
        self.position += self.chunk_size
        return self.data[self.position - self.chunk_size: self.position]

    def has_data(self):
        return self.position + self.chunk_size * 2 <= len(self.data)

    def total_chunk(self):
        return len(self.data) / self.chunk_size


class Anylyzer(object):
    def __init__(self, music_path, frame_rate, least_energy, pin_list, response_time, speed, on_tft=False):
        sample_rate, music_data = read(music_path)
        if music_data.shape[1] == 2:  # two channels
            music_data = (music_data[:, 0] + music_data[:, 1]) / 2

        keyboard.key_initiate(pin_list)
        self.pin_list = pin_list
        self.frame_rate = frame_rate
        self.least_energy = least_energy
        self.least_length = int(speed * frame_rate * response_time)
        self.data = Data(music_data, int(sample_rate / frame_rate))
        self.sample_rate = sample_rate
        self.main_thread_queue = Queue.Queue()
        self.visualizer = Visualizer(speed, on_tft)
        self.running = False
        self.future_states = []

    def _refresh(self, current_frame, future_frame):
        return self.visualizer.real_time_refresh(current_frame, future_frame,
                                                 keyboard.key_status(self.pin_list))

    def _terminate(self):
        self.running = False

    def _fft(self):
        data = self.data.next_chunk()
        freq_domain = np.fft.fft(data) / len(data)
        freq_domain = freq_domain[range(len(data) / 2)]
        max_bin = np.argmax(np.abs(freq_domain[1:]))

        if np.abs(freq_domain[max_bin]) > self.least_energy:
            return (max_bin + 1) * (self.sample_rate / len(data))
        else:
            return None

    def _analyze(self):
        # if there is no data left after this time, terminate the loop after FFT
        should_quit = not self.data.has_data()
        if not should_quit and self.running:
            threading.Timer(1.0 / self.frame_rate, self._analyze).start()

        self.main_thread_queue.put([self._refresh, self.future_states[0],
                                    [np.sum((np.array(self.future_states))[:, i]) == self.least_length
                                     for i in range(4)]])

        del self.future_states[0]
        max_freq = self._fft()
        new_frame = [0] * 4
        if max_freq:
            new_frame[max_freq >= 1000 and 3 or int(max_freq / 250)] = 1
        self.future_states.append(new_frame)

        if should_quit:
            self.main_thread_queue.put([self._terminate])

    def real_time_analyze(self):
        assert self.data.total_chunk() >= self.least_length

        self.running = True
        self.future_states = [[0] * 4] * self.least_length
        self._analyze()

        while self.running:
            try:
                items = self.main_thread_queue.get()
                if len(items) == 1:
                    items[0]()
                else:
                    func = items[0]
                    args = items[1:]
                    self.running = func(*args)

            except KeyboardInterrupt:
                self._terminate()

        keyboard.key_clean()


if __name__ == "__main__":
    analyzer = Anylyzer("peace.wav", 60, 100, [17, 22, 23, 27], 0.01, 2)
    analyzer.real_time_analyze()
