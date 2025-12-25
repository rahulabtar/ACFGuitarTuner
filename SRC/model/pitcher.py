import numpy as np
import enum

class PitchMethod(enum.Enum):
    ACF = 1
    AMDF = 2
    YIN = 3


class Pitcher:
    def __init__(self):
        self.buffer = None
        self.buffer_size = None
        self.sampleRate = None
        self.method = None

        # Pitch range (Hz)
        self.f_min = 50.0
        self.f_max = 500.0

    def setBufferSize(self, size):
        self.buffer_size = size

    def setSampleRate(self, sampleRate):
        self.sampleRate = sampleRate

    def setMethod(self, method: PitchMethod):
        self.method = method

    def loadBuffer(self, block):
        num_samples = len(block)
        self.buffer = np.roll(self.buffer, -num_samples)
        self.buffer[-num_samples:] = block

    def getPitch(self):
        if not self.is_note_active(db_threshold=40):
            return None
        if self.method == PitchMethod.ACF:
            pitch = self._getPitchACF()
            return pitch
        return None


    def is_note_active(self, db_threshold=40):
        """
        Return True if the buffer contains a note above the threshold.
        Threshold is in dB SPL.
        """
        if self.buffer is None:
            return False
        db = self.get_DBSPL()
        return db > db_threshold


    # --------------------------------------------------
    # ACF with Hann window + interpolation
    # --------------------------------------------------
    def _getPitchACF(self):
        if self.buffer is None:
            return None

        window = np.hanning(len(self.buffer))
        x = self.buffer * window

        corrs, lag_min = self._getCorr(x)

        peaks = self._findLocalMaxima(corrs)
        if len(peaks) == 0:
            return None

        peak = peaks[0]

        # Strength of the peak relative to zero-lag (energy)
        peak_strength = corrs[peak] / corrs[0]
        if peak_strength < 0.3:  # empirical threshold
            return None  # Weak correlation → probably no note

        # Parabolic interpolation
        if 1 <= peak < len(corrs) - 1:
            y_m1 = corrs[peak - 1]
            y_0  = corrs[peak]
            y_p1 = corrs[peak + 1]
            denom = (y_m1 - 2 * y_0 + y_p1)
            delta = 0.5 * (y_m1 - y_p1) / denom if denom != 0 else 0.0
        else:
            delta = 0.0

        refined_lag = peak + delta + lag_min
        return self.sampleRate / refined_lag

    
    def _ACF(self, x, lag):
        return np.sum(x[:-lag] * x[lag:])

    def _getCorr(self, x):
        fs = self.sampleRate

        lag_min = int(fs / self.f_max)
        lag_max = int(fs / self.f_min)

        corrs = np.zeros(lag_max - lag_min)

        for i, lag in enumerate(range(lag_min, lag_max)):
            corrs[i] = self._ACF(x, lag)

        return corrs, lag_min

    def _findLocalMaxima(self, x):
        return [
            i for i in range(1, len(x) - 1)
            if x[i] > x[i - 1] and x[i] > x[i + 1]
        ]

    # --------------------------------------------------
    # Utilities
    # --------------------------------------------------
    def getCentsError(self, fn, freqCalc):
        return 1200 * np.log2(freqCalc / fn)

    def get_DBSPL(self):
        rms = np.sqrt(np.mean(self.buffer ** 2))
        return 20 * np.log10(rms / 0.00002)
