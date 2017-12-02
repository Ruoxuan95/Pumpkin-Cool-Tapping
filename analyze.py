import os
import multiprocessing
import numpy as np
import visualize
import keyboard
from time import time, sleep


class Analyzer(object):
    def __init__(self, music_path, sample_rate, frame_rate, least_energy, pin_list, response_time,
                 speed=2, on_tft=False):
        stats_file = "{}.npy".format(os.path.splitext(music_path))

        # if the music has not been processed before
        if not os.path.isfile(stats_file):
            print("Loading Essentia module...")
            import essentia.standard as ess_std
            self.module = ess_std

            print("Loading music...")
            loader = self.module.MonoLoader(filename=music_path)
            audio = loader()

            pool = multiprocessing.Pool()
            num_process = multiprocessing.cpu_count()
            stats = [None] * num_process
            segment_length = int(len(audio) / num_process)

            print("Calculating onsets...")
            processing_start = time()
            for i in range(num_process):
                pool.apply_async(self._detect_onset, args=(
                    audio[segment_length * i: min(segment_length * (i + 1), len(audio))], stats, i))

            pool.close()
            pool.join()

            detected_onsets = np.array([len(audio)])  # the first element stores the number of frames
            [np.append(detected_onsets, stats[i] + i * segment_length / sample_rate) for i in range(num_process)]
            np.append(detected_onsets, np.finfo(np.float).max)  # so that read_onset will never reach len(self.onsets)
            np.save(stats_file, detected_onsets)

            self.num_frames = len(audio)
            self.onsets = detected_onsets[1:]
            print("Onset detection finished. Elapsed time: {:.2f}s".format(time() - processing_start))

        else:
            stats = np.load(stats_file)
            self.num_frames = stats[0]
            self.onsets = stats[1:]
            print("Pre-processing skipped")

        keyboard.key_initiate(pin_list)
        self.pin_list = pin_list
        self.time_interval = 1.0 / frame_rate
        self.least_energy = least_energy
        self.sample_rate = sample_rate
        self.visualizer = visualize.Visualizer(music_path, int(speed * frame_rate * response_time), speed, on_tft)

    def _detect_onset(self, audio, collector, index):
        processing_start = time()
        onset_detector = self.module.OnsetDetection(method="complex")
        window = self.module.Windowing(type="hann")
        fft = self.module.FFT()
        c2p = self.module.CartesianToPolar()
        onsets = self.module.Onsets()

        frames = []
        for frame in self.module.FrameGenerator(audio, frameSize=1024, hopSize=512):
            mag, phase = c2p(fft(window(frame)))
            frames.append(onset_detector(mag, phase))

        collector[index] = onsets(np.array(frames), [1])
        print("Subprocess finished. Elapsed time: {:.2}s".format(time() - processing_start))

    def __call__(self):
        cross_screen = (visualize.height - visualize.verify_height) / self.visualizer.speed
        self.history_onset = [0] * cross_screen
        timestamp = time()
        display_start = time()
        counter = 0
        read_onset = 0

        try:
            for i in xrange(self.num_frames):
                counter += 1
                if counter == cross_screen - 30:
                    self.visualizer.play_music()

                frame = [0] * 4
                if self.history_onset[0]:
                    frame[np.random.randint(0, 4)] = 1
                clicked = self.visualizer.detection_refresh(frame, keyboard.key_status(self.pin_list))

                del self.history_onset[0]
                if time() - display_start > self.onsets[read_onset]:
                    self.history_onset.append(True)
                    read_onset += 1
                else:
                    self.history_onset.append(False)

                if not clicked:
                    sleep_time = timestamp + self.time_interval - time()
                    if sleep_time > 0:
                        sleep(sleep_time)
                    timestamp += self.time_interval
                else:
                    break

        except KeyboardInterrupt:
            pass

        finally:
            keyboard.key_clean()
            print("Elapsed time: {:.2f}s".format(time() - display_start))


if __name__ == "__main__":
    analyzer = Analyzer("JULY.mp3", 44100, 60, 0, [17, 22, 23, 27], 0.01)
    analyzer()
