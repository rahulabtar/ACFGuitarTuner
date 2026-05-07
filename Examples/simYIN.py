import numpy as np
import csv

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
    # Avoid divide by zero for very short buffers
    with np.errstate(divide='ignore', invalid='ignore'):
        norm[1:] = np.where(cumsum > 0,
                            asmdf[1:] * np.arange(1, len(asmdf)) / cumsum,
                            1)
    return norm

def _absoluteThreshold(cmnd, threshold=0.15):
    """
    Step 3: Find the first lag that dips below threshold,
    then walk to the bottom of that dip.
    Falls back to global minimum if no lag clears the threshold.
    """
    for lag in range(2, len(cmnd)):
        if cmnd[lag] < threshold:
            while lag + 1 < len(cmnd) and cmnd[lag + 1] < cmnd[lag]:
                lag += 1
            return lag
    return int(np.argmin(cmnd[2:]) + 2)

def _parabolicInterpOnAsmdf(asmdf, lag):
    """Refine lag using the raw ASMDF rather than the normalized CMND."""
    if lag <= 0 or lag >= len(asmdf) - 1:
        return float(lag)
    denom = asmdf[lag - 1] - 2 * asmdf[lag] + asmdf[lag + 1]
    if denom == 0:
        return float(lag)
    return lag + 0.5 * (asmdf[lag - 1] - asmdf[lag + 1]) / denom


# --- Main YIN function ---

def yin(samps, fs, threshold=0.15):
    asmdf = _fft_asmdf(samps)
    cmnd  = _cmndf(asmdf)
    lag   = _absoluteThreshold(cmnd, threshold)
    refined_lag = _parabolicInterpOnAsmdf(asmdf, lag)  # <-- change here

    if refined_lag < 1:
        return 0
    return fs / refined_lag

# --- Helpers ---

def genSin(f, fs, numSamp):
    n = np.arange(0, numSamp)
    return np.sin(2 * np.pi * (f / fs) * n)

def getCentsError(fn, freqCalc):
    if freqCalc <= 0:
        return "div/0 error"
    return 1200 * np.log2(freqCalc / fn)

# --- Main ---

with open('YINTest48khz.csv', 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['Sampling Frequency', 'True Frequency', 'Frequency Calculated', 'Cents Error'])

    fs = 48000
    for fn in range(50, 1000, 50):
        numSamps = round(fs / fn * 10)
        samps = genSin(fn, fs, numSamps)
        freqCalc = yin(samps, fs, threshold=0.15)
        centserror = getCentsError(fn, freqCalc)
        csvwriter.writerow([fs, fn, freqCalc, centserror])

    print("Done")

# with open('YINTest48khz.csv', 'w', newline='') as csvfile:
#     csvwriter = csv.writer(csvfile)
#     csvwriter.writerow(['Sampling Frequency', 'True Frequency', 'Num Periods', 'Frequency Calculated', 'Cents Error'])

#     fs = 48000
#     for fn in range(50, 1000, 50):
#         for numPeriods in range(1, 11):
#             numSamps = round(fs / fn * numPeriods)
#             samps = genSin(fn, fs, numSamps)
#             freqCalc = yin(samps, fs, threshold=0.15)
#             centserror = getCentsError(fn, freqCalc)
#             csvwriter.writerow([fs, fn, numPeriods, freqCalc, centserror])

#     print("Done")