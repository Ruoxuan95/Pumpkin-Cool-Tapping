import numpy as np
import matplotlib.pyplot as plt
from scipy.io.wavfile import read


sample_rate, data = read("sample.wav")
s = np.fft.fft(data) / len(data)
s = s[range(len(data) / 2)]
freq = [i for i in range(10000, 20000)]
plt.plot(freq, abs(s)[10000: 20000])
plt.show()
