import os
import multiprocessing
import numpy as np
import visualize
import keyboard
from time import time, sleep


# https://stackoverflow.com/a/46266853/7873124
# put declaration outside of the Analyzer class
# multiprocess cannot pickle an undefined function
def detect_onset(audio, index):
    # should be able to fetch the module from cache
    import essentia.standard as ess_std
    from essentia import array

    print("Subprocess {} starts".format(index))
    processing_start = time()

    onset_detector = ess_std.OnsetDetection(method="complex")
    window = ess_std.Windowing(type="hann")
    fft = ess_std.FFT()
    c2p = ess_std.CartesianToPolar()
    onsets = ess_std.Onsets()

    frames = []
    for frame in ess_std.FrameGenerator(audio, frameSize=1024, hopSize=512):
        mag, phase = c2p(fft(window(frame)))
        frames.append(onset_detector(mag, phase))

    onsets_array = onsets(array([frames]), [1])
    print("Subprocess {} finished. Elapsed time: {:.2}s".format(index, time() - processing_start))
    return onsets_array


class Analyzer(object):
    def __init__(self, music_path, sample_rate, frame_rate, least_energy, pin_list, response_time,
                 speed=2, on_tft=False, screen=None):
        keyboard.key_initiate(pin_list)
        self.pin_list = pin_list
        self.frame_rate = frame_rate
        self.time_interval = 1.0 / frame_rate
        self.least_energy = least_energy
        self.sample_rate = sample_rate
        self.music_path = music_path
        self.visualizer = visualize.Visualizer(music_path, int(speed * frame_rate * response_time), speed, on_tft, screen)

        stats_file = "{}.npz".format(os.path.splitext(music_path)[0])
        # if the music has not been processed before
        if not os.path.isfile(stats_file):
            print("Loading Essentia module...")
            import essentia.standard as ess_std

            print("Loading music...")
            loader = ess_std.MonoLoader(filename=music_path)
            audio = loader()

            pool = multiprocessing.Pool()
            num_process = multiprocessing.cpu_count()
            segment_length = int(len(audio) / num_process) / 1024 * 1024

            onset_collector = []
            self.num_frames = len(audio)

            print("Calculating onsets...")
            processing_start = time()

            results = [None] * num_process
            for i in range(num_process):
                results[i] = pool.apply_async(detect_onset, args=(
                    audio[segment_length * i: min(segment_length * (i + 1), len(audio))], i))
            pool.close()
            pool.join()

            for i in range(num_process):
                onsets = results[i].get() + i * float(segment_length) / self.sample_rate
                onset_collector += onsets.tolist()

            onset_collector.append(np.finfo(float).max)  # so that read_onset will never reach len(self.onsets)
            self.onsets = np.array(onset_collector)

            print("Onset detection finished. Elapsed time: {:.2f}s".format(time() - processing_start))
            np.savez(os.path.splitext(music_path)[0], num_frames=np.array([self.num_frames]), onsets=self.onsets)

        else:
            stats = np.load(stats_file)
            self.num_frames = stats["num_frames"][0]
            self.onsets = stats["onsets"]
            print("Pre-processing skipped")

    def __call__(self):
        timestamp = time()
        display_start = time()
        read_onset = 0
        counter = 0

        try:
            for i in xrange(int(self.num_frames / float(self.sample_rate) * self.frame_rate)):
                counter += 1
                if counter == self.visualizer.cross_screen:
                    self.visualizer.play_music()

                frame = [0] * 4
                if time() - display_start > self.onsets[read_onset]:
                    read_onset += 1
                    frame[np.random.randint(0, 4)] = 1
                clicked = self.visualizer.detection_refresh(frame, keyboard.key_status(self.pin_list))

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
            self.visualizer.stop_music()
            keyboard.key_clean()
            print("Elapsed time: {:.2f}s".format(time() - display_start))


if __name__ == "__main__":
    analyzer = Analyzer("locked.mp3", 44100, 60, 0, [26, 13, 6, 5], 0.05)
    analyzer()
