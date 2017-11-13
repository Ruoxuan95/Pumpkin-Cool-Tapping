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
        old_position = self.position
        self.position = min(self.position + self.chunk_size, len(self.data))
        return self.data[old_position: self.position]

    def has_data(self):
        return self.position + self.chunk_size < len(self.data)


class Anylyzer(object):
    def __init__(self, music_path, frame_rate, pin_list, response_time, speed, on_tft=True):
        sample_rate, music_data = read(music_path)
        if music_data.shape[1] == 2:  # two channels
            music_data = (music_data[:, 0] + music_data[:, 1]) / 2

        keyboard.key_initiate(pin_list)
        self.pin_list = pin_list
        self.frame_rate = frame_rate
        self.least_length = int(speed * frame_rate * response_time)
        self.data = Data(music_data, int(sample_rate / frame_rate))
        self.main_thread_queue = Queue.Queue()
        self.visualizer = Visualizer(speed, on_tft)
        self.running = False
        self.future_states = []

    def _refresh(self, visualizer, current_frame, future_frames):
        return visualizer.refresh_real_time(current_frame, future_frames, keyboard.key_status(self.pin_list))

    def _terminate(self):
        self.running = False

    def _fft(self, data):
        freq_domain = np.fft.fft(data) / len(data)
        freq_domain = freq_domain[range(len(data) / 2)]
        max_freq = np.argmax(abs(freq_domain[1:]))

        frame = [0] * 4
        frame[int(max_freq / 5) > 3 and 3 or int(max_freq / 5)] = 1

        return frame

    def _analyze(self, interval, data_chunks, callback_queue, visualizer):
        # if there is no data left after this time, terminate the loop after FFT
        should_quit = not data_chunks.has_data()
        if not should_quit and self.running:
            threading.Timer(interval, self._analyze,
                            [interval, data_chunks, callback_queue, visualizer]).start()

        del self.future_states[0]
        self.future_states.append(self._fft(data_chunks.next_chunk()))
        current_frame = self.future_states[0]

        callback_queue.put([self._refresh, visualizer, current_frame,
                            [np.sum((np.array(self.future_states))[:, i]) == self.least_length for i in range(4)]])

        if should_quit:
            callback_queue.put([self._terminate])

    def start_analyze(self):
        self.running = True

        self.future_states.append([0, 0, 0, 0])  # dummy state
        [self.future_states.append(self._fft(self.data.next_chunk())) for i in range(self.least_length - 1)]
        self._analyze(1.0 / self.frame_rate, self.data, self.main_thread_queue, self.visualizer)

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
                self.running = False

        keyboard.key_clean()


if __name__ == "__main__":
    analyzer = Anylyzer("peace.wav", 60, [17, 22, 23, 27], 0.2, 2)
    analyzer.start_analyze()
