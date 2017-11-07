import numpy as np
from scipy.io.wavfile import read
import visualize
import keyboard


def read_wav(file_path, chunk_size=1000):
    sample_rate, data = read(file_path)
    if data.shape[1] == 2:  # two channels
        data = (data[:, 0] + data[:, 1]) / 2
    for i in range(len(data) / chunk_size):
        yield data[i * chunk_size: min((i + 1) * chunk_size, len(data))]


if __name__ == "__main__":
    visualizer = visualize.Visualizer(True)
    all_pin = [17, 22, 23, 27]
    keyboard.key_initiate(all_pin)

    try:
        for chunk in read_wav("sample.wav"):
            freq_domain = np.fft.fft(chunk) / len(chunk)
            freq_domain = freq_domain[range(len(chunk) / 2)]
            max_freq = np.argmax(abs(freq_domain))

            frame = [0]*4
            frame[int(max_freq / 25) > 3 and 3 or int(max_freq / 25)] = 1

            visualizer.refresh(frame, keyboard.key_status(all_pin))
            visualizer.tick()

    except KeyboardInterrupt:
        pass

    finally:
        keyboard.key_clean()
