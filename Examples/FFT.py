import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile

def loadWav(path):
    fs, data = wavfile.read(path)
    data = data.astype(np.float32)
    data /= np.max(np.abs(data))
    return fs, data

# --- Load and take a single frame from the start of the note ---

audioPath = 'Assets/TestSounds/400sin.wav'
fs, samps = loadWav(audioPath)

frameSize = round(fs * 0.15)
frame     = samps[0:frameSize]

# --- FFT ---

fft    = np.fft.rfft(frame)
mag    = np.abs(fft)
freqs  = np.fft.rfftfreq(len(frame), d=1/fs)

# --- Plot ---

plt.figure(figsize=(12, 5))
plt.plot(freqs, mag)

# Mark expected harmonics
E1 = 41.2
for i, harmonic in enumerate([E1, E1*2, E1*3, E1*4]):
    plt.axvline(x=harmonic, color='red', linestyle='--', alpha=0.7,
                label=f'E1 x{i+1} ({harmonic:.1f} Hz)' if i < 4 else '')

plt.xlim(0, 500)       # focus on the low frequency region
plt.xlabel('Frequency (Hz)')
plt.ylabel('Magnitude')
plt.title('FFT of MalletGuitarE1 — First 150ms')
plt.legend()
plt.tight_layout()
plt.savefig('Assets/TestResults/MalletGuitarE1_FFT.png', dpi=150)
plt.show()
print("Done")