import numpy as np
from scipy.io.wavfile import read
import visualize
import keyboard
from aubio import source, tempo, onset
from time import time, sleep


class MusicData(object):
    def __init__(self, music_path, frame_rate):
        self.sample_rate, self.data = read(music_path)
        self.window_size = int(self.sample_rate / frame_rate) * 2
        self.hop_size = self.window_size // 2
        self.source = source(music_path, self.sample_rate, self.hop_size)
        self.position = 0

    def next_chunk(self):
        chunk = self.data[self.position: self.position + self.window_size]
        self.position += self.hop_size
        return chunk, self.source()[0]

    def has_data(self):
        return self.position + self.window_size <= len(self.data)


class Analyzer(object):
    def __init__(self, wav_path, mp3_path, frame_rate, least_energy, pin_list, response_time, speed, on_tft=False):
        keyboard.key_initiate(pin_list)
        self.pin_list = pin_list
        self.frame_rate = frame_rate
        self.least_energy = least_energy
        self.least_length = int(speed * frame_rate * response_time)
        self.data = MusicData(wav_path, frame_rate)
        self.sample_rate = self.data.sample_rate
        self.visualizer = visualize.Visualizer(speed, on_tft)
        self.visualizer.load_music(mp3_path)
        self.running = False
        self.future_notes = []
        self.history_beats = []
        self.history_onset = []
        self.tempo = tempo("mkl", self.data.window_size, self.data.hop_size, self.data.sample_rate)
        self.onset = onset("default", self.data.window_size, self.data.hop_size, self.data.sample_rate)

    def _fft(self, data):
        freq_domain = np.fft.fft(data) / len(data)
        freq_domain = freq_domain[range(len(data) / 2)]
        max_bin = np.argmax(np.abs(freq_domain[1:]))

        if np.abs(freq_domain[max_bin]) > self.least_energy:
            return (max_bin + 1) * (self.sample_rate / len(data))
        else:
            return None

    def _detect_beat(self, data):
        if self.tempo(data):
            return self.tempo.get_confidence()
        else:
            return None

    def _detect_onset(self, data):
        if self.onset(data):
            return self.onset.get_last()
        else:
            return None

    def _analyze(self):
        fft_data, melody_data = self.data.next_chunk()

        max_freq = self._fft(fft_data)
        new_frame = [0] * 4
        if max_freq:
            new_frame[max_freq >= 1000 and 3 or int(max_freq / 250)] = 1
        del self.future_notes[0]
        self.future_notes.append(new_frame)

        if self.history_beats[0]:
            print "{} found beat. confidence {}".format(time(), self.history_beats[0])
        if self.history_onset[0]:
            print "{} found onset {}".format(time(), self.history_onset[0])

        clicked = self.visualizer.real_time_refresh(self.future_notes[0],
                                                    [np.sum((np.array(self.future_notes))[:, i]) ==
                                                     self.least_length for i in range(4)],
                                                    keyboard.key_status(self.pin_list),
                                                    self.history_beats[0], self.history_onset[0])
        del self.history_beats[0]
        self.history_beats.append(self._detect_beat(melody_data))
        del self.history_onset[0]
        self.history_onset.append(self._detect_onset(melody_data))

        return self.data.has_data() and not clicked

    def real_time_analyze(self):
        cross_screen = (visualize.height - visualize.verify_height) / self.visualizer.speed
        self.future_notes = [[0] * 4] * self.least_length
        self.history_beats = [0] * cross_screen
        self.history_onset = [0] * cross_screen

        running = True
        timestamp = time()
        counter = 0
        while running:
            try:
                running = self._analyze()

                counter += 1
                if counter == cross_screen - 30:
                    self.visualizer.play_music()

                while time() - timestamp < 1.0 / self.frame_rate:
                    sleep(0.00001)
                timestamp += 1.0 / self.frame_rate

            except KeyboardInterrupt:
                running = False

        keyboard.key_clean()


if __name__ == "__main__":
    analyzer = Analyzer("JULY.wav", "JULY.mp3", 60, 0, [17, 22, 23, 27], 0.01, 2)
    analyzer.real_time_analyze()
