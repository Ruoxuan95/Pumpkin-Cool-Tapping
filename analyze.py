import numpy as np
from scipy.io.wavfile import read
from visualize import Visualizer
import keyboard
import threading
import Queue
from aubio import tempo
from time import time


class Data(object):
    def __init__(self, data_chunks, window_size, hop_size):
        self.position = 0
        self.data = data_chunks
        self.window_size = window_size
        self.hop_size = hop_size

    def next_chunk(self):
        chunk = self.data[self.position: self.position + self.window_size]
        self.position += self.hop_size
        return chunk

    def has_data(self):
        return self.position + self.hop_size + self.window_size <= len(self.data)

    def total_chunk(self):
        return (len(self.data) - self.window_size + self.hop_size) / self.hop_size


class Anylyzer(object):
    def __init__(self, music_path, frame_rate, least_energy, pin_list, response_time, speed, on_tft=False):
        sample_rate, music_data = read(music_path)
        hop_size, window_size = [int(sample_rate / frame_rate) * i for i in [1, 2]]
        if music_data.shape[1] == 2:  # two channels
            music_data = (music_data[:, 0] + music_data[:, 1]) / 2

        keyboard.key_initiate(pin_list)
        self.pin_list = pin_list
        self.frame_rate = frame_rate
        self.least_energy = least_energy
        self.least_length = int(speed * frame_rate * response_time)
        self.data = Data(music_data, window_size, hop_size)
        self.sample_rate = sample_rate
        self.main_thread_queue = Queue.Queue()
        self.visualizer = Visualizer(speed, on_tft)
        self.running = False
        self.future_notes = []
        self.tempo = tempo("specdiff", window_size, hop_size, sample_rate)

    def _refresh(self, current_frame, future_frame):
        return self.visualizer.real_time_refresh(current_frame, future_frame,
                                                 keyboard.key_status(self.pin_list))

    def _terminate(self):
        self.running = False

    def _fft(self, data):
        freq_domain = np.fft.fft(data) / len(data)
        freq_domain = freq_domain[range(len(data) / 2)]
        max_bin = np.argmax(np.abs(freq_domain[1:]))

        if np.abs(freq_domain[max_bin]) > self.least_energy:
            return (max_bin + 1) * (self.sample_rate / len(data))
        else:
            return None
    
    def _detect_beat(self, data):
        return self.tempo(data) and self.tempo.get_confidence() > 0.8

    def _analyze(self):
        # if there is no data left after this time, terminate the loop after FFT
        should_quit = not self.data.has_data()
        if not should_quit and self.running:
            threading.Timer(1.0 / self.frame_rate, self._analyze).start()

        self.main_thread_queue.put([self._refresh, self.future_notes[0],
                                    [np.sum((np.array(self.future_notes))[:, i]) == self.least_length
                                     for i in range(4)]])

        new_data = self.data.next_chunk()

        max_freq = self._fft(new_data)
        new_frame = [0] * 4
        if max_freq:
            new_frame[max_freq >= 1000 and 3 or int(max_freq / 250)] = 1
        del self.future_notes[0]
        self.future_notes.append(new_frame)

        if self._detect_beat(new_data):
            print "{} found beat".format(time())

        if should_quit:
            self.main_thread_queue.put([self._terminate])

    def real_time_analyze(self):
        assert self.data.total_chunk() >= self.least_length

        self.running = True
        self.future_notes = [[0] * 4] * self.least_length
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
    start = time()
    analyzer = Anylyzer("peace.wav", 60, 100, [17, 22, 23, 27], 0.01, 2)
    analyzer.real_time_analyze()
    print time() - start
