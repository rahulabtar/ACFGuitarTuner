import numpy as np
import csv
from scipy.io import wavfile

# --- Low-level DSP ---

def _fft_acf(samps):
    """Compute ACF for all lags via FFT. O(n log n)."""
    n = len(samps)
    fft = np.fft.rfft(samps, n=2 * n)
    power = fft * np.conj(fft)
    return np.fft.irfft(power)[:n].real

def _fft_asmdf(samps):
    """
    Compute ASMDF for all lags via FFT using the identity:
    ASMDF(lag) = 2 * (ACF(0) - ACF(lag))
    """
    acf = _fft_acf(samps)
    return 2 * (acf[0] - acf)

# --- YIN Steps ---

def _cmndf(asmdf):
    """
    Step 2: Cumulative Mean Normalized Difference.
    Removes bias toward short lags.
    """
    norm = np.zeros(len(asmdf))
    norm[0] = 1
    cumsum = np.cumsum(asmdf[1:])
    with np.errstate(divide='ignore', invalid='ignore'):
        norm[1:] = np.where(cumsum > 0,
                            asmdf[1:] * np.arange(1, len(asmdf)) / cumsum,
                            1)
    return norm

def _absoluteThreshold(cmnd, threshold=0.15, lagMin=2, lagMax=None):
    """
    Step 3: Find the first lag that dips below threshold,
    then walk to the bottom of that dip.
    Falls back to global minimum if no lag clears the threshold.
    lagMin/lagMax constrain the search to a frequency range of interest,
    preventing octave errors from harmonics outside that range.
    """
    end = lagMax if lagMax is not None else len(cmnd)
    for lag in range(lagMin, end):
        if cmnd[lag] < threshold:
            while lag + 1 < end and cmnd[lag + 1] < cmnd[lag]:
                lag += 1
            return lag
    return int(np.argmin(cmnd[lagMin:end]) + lagMin)

def _parabolicInterpOnAsmdf(asmdf, lag):
    """Refine lag using the raw ASMDF rather than the normalized CMND."""
    if lag <= 0 or lag >= len(asmdf) - 1:
        return float(lag)
    denom = asmdf[lag - 1] - 2 * asmdf[lag] + asmdf[lag + 1]
    if denom == 0:
        return float(lag)
    return lag + 0.5 * (asmdf[lag - 1] - asmdf[lag + 1]) / denom

# --- Silence Detection ---

def isSilent(frame, rmsThreshold=0.01):
    """
    Returns True if the frame's RMS energy is below the threshold.
    Prevents YIN from returning garbage frequencies on silent frames.
    """
    return np.sqrt(np.mean(frame ** 2)) < rmsThreshold

# --- Main YIN function ---

def yin(samps, fs, threshold=0.15, fMin=30, fMax=100):
    """
    Estimate fundamental frequency using the YIN algorithm.
    fMin/fMax define the expected frequency range, preventing octave errors
    by constraining the lag search window.
    Returns frequency in Hz, or 0 if unvoiced/no pitch found.
    """
    asmdf  = _fft_asmdf(samps)
    cmnd   = _cmndf(asmdf)

    lagMin = max(2, round(fs / fMax))
    lagMax = min(len(cmnd), round(fs / fMin))

    lag         = _absoluteThreshold(cmnd, threshold, lagMin, lagMax)
    refined_lag = _parabolicInterpOnAsmdf(asmdf, lag)

    if refined_lag < 1:
        return 0
    return fs / refined_lag

# --- Audio Loading ---

def loadWav(path):
    """
    Load a WAV file and normalize to [-1, 1] float32.
    Returns (fs, samples).
    """
    fs, data = wavfile.read(path)
    data = data.astype(np.float32)
    data /= np.max(np.abs(data))
    return fs, data

# --- Framed Analysis ---

def analyzeFile(path, frameSizeSecs=0.15, hopSizeSecs=0.01,
                yinThreshold=0.15, silenceThreshold=0.001,
                fMin=30, fMax=800):
    """
    Run YIN on overlapping frames of an audio file.
    Returns list of (timeStamp, frequency) tuples and the sample rate.
    """
    fs, samps = loadWav(path)
    frameSize = round(fs * frameSizeSecs)
    hopSize   = round(fs * hopSizeSecs)

    results = []
    for start in range(0, len(samps) - frameSize, hopSize):
        frame     = samps[start : start + frameSize]
        timeStamp = start / fs

        if isSilent(frame, silenceThreshold):
            results.append((timeStamp, 0))
            continue

        freqCalc = yin(frame, fs, threshold=yinThreshold, fMin=fMin, fMax=fMax)
        results.append((timeStamp, freqCalc))

    return results, fs

# --- Helpers ---

def getCentsError(fn, freqCalc):
    if freqCalc <= 0:
        return "unvoiced"
    return round(1200 * np.log2(freqCalc / fn), 4)

# --- Main ---

audioPath = 'Assets/TestSounds/400sin.wav'
results, fs = analyzeFile(
    audioPath,
    frameSizeSecs=0.15,
    hopSizeSecs=0.01,
    yinThreshold=0.1,
    silenceThreshold=0.001,
    fMin=30,
    fMax=800
)

E3 = 400  # Hz

with open('Assets/TestResults/400sin.csv', 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['Time (s)', 'Frequency (Hz)', 'Cents Error vs E3'])

    for timeStamp, freq in results:
        centsErr = getCentsError(E3, freq)
        csvwriter.writerow([round(timeStamp, 4), round(freq, 3), centsErr])

print(f"Done — {len(results)} frames analyzed, output written to Assets/TestResults/YIN_MalletGuitarE1.csv")

# def yinDebug(samps, fs, threshold=0.15, fMin=30, fMax=500):
#     asmdf  = _fft_asmdf(samps)
#     cmnd   = _cmndf(asmdf)

#     lagMin = max(2, round(fs / fMax))
#     lagMax = min(len(cmnd), round(fs / fMin))

#     print(f"\n--- Debug ---")
#     print(f"fs={fs}, fMin={fMin}, fMax={fMax}")
#     print(f"lagMin={lagMin} ({fs/lagMin:.1f} Hz), lagMax={lagMax} ({fs/lagMax:.1f} Hz)")
#     print(f"CMND min in window: {np.min(cmnd[lagMin:lagMax]):.4f} at lag {np.argmin(cmnd[lagMin:lagMax]) + lagMin}")
#     print(f"CMND values around E1 lag ({round(fs/41.2)}):")
#     e1lag = round(fs / 41.2)
#     for l in range(e1lag - 3, e1lag + 4):
#         if 0 < l < len(cmnd):
#             print(f"  lag {l} ({fs/l:.2f} Hz): CMND={cmnd[l]:.4f}, ASMDF={asmdf[l]:.4f}")

# # Run on the first non-silent frame
# fs, samps = loadWav('Assets/TestSounds/400sin.wav')
# frameSize = round(fs * 0.15)
# frame = samps[0:frameSize]
# yinDebug(frame, fs)