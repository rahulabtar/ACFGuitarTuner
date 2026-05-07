import numpy as np
import enum


class PitchMethod(enum.Enum):
    ACF = 1
    YIN = 2


class Pitcher:
    def __init__(self):
        self.buffer = None
        self.buffer_size = None
        self.sampleRate = None
        self.method = None

        self.f_min = 30.0
        self.f_max = 800.0

        # YIN
        self.yinThreshold = 0.1

        # Silence
        self.silenceThreshold = 0.001  # RMS

    # --------------------------------------------------
    # Configuration
    # --------------------------------------------------

    def setBufferSize(self, size):
        self.buffer_size = size
        self.buffer = np.zeros(size)

    def setSampleRate(self, sampleRate):
        self.sampleRate = sampleRate

    def setMethod(self, method: PitchMethod):
        self.method = method

    def setYinThreshold(self, threshold):
        self.yinThreshold = threshold

    def setFrequencyRange(self, f_min, f_max):
        self.f_min = f_min
        self.f_max = f_max

    # --------------------------------------------------
    # Buffer management
    # --------------------------------------------------

    def loadBuffer(self, block):
        num_samples = len(block)
        self.buffer = np.roll(self.buffer, -num_samples)
        self.buffer[-num_samples:] = block

    # --------------------------------------------------
    # Public pitch API
    # --------------------------------------------------

    def getPitch(self):
        if self.buffer is None:
            return None
        if self.isSilent():
            return None
        if self.method == PitchMethod.ACF:
            return self._getPitchACF()
        if self.method == PitchMethod.YIN:
            return self._getPitchYIN()
        return None

    def isSilent(self):
        if self.buffer is None:
            return True
        return np.sqrt(np.mean(self.buffer ** 2)) < self.silenceThreshold

    # --------------------------------------------------
    # ACF pipeline
    # --------------------------------------------------

    def _getPitchACF(self):
        window = np.hanning(len(self.buffer))
        x = self.buffer * window

        corrs, lag_min = self._getACFCorr(x)
        peaks = self._findLocalMaxima(corrs)
        if len(peaks) == 0:
            return None

        peak = peaks[0]
        if corrs[peak] / corrs[0] < 0.3:
            return None

        delta = self._parabolicInterpACF(corrs, peak)
        return self.sampleRate / (peak + delta + lag_min)

    def _fft_acf(self, samps):
        """Compute ACF for all lags via FFT. O(n log n)."""
        n = len(samps)
        fft = np.fft.rfft(samps, n=2 * n)
        power = fft * np.conj(fft)
        return np.fft.irfft(power)[:n].real

    def _getACFCorr(self, x):
        lag_min = int(self.sampleRate / self.f_max)
        lag_max = int(self.sampleRate / self.f_min)
        corrs = np.zeros(lag_max - lag_min)
        for i, lag in enumerate(range(lag_min, lag_max)):
            corrs[i] = np.sum(x[:-lag] * x[lag:])
        return corrs, lag_min

    def _parabolicInterpACF(self, corrs, peak):
        if 1 <= peak < len(corrs) - 1:
            y_m1, y_0, y_p1 = corrs[peak - 1], corrs[peak], corrs[peak + 1]
            denom = y_m1 - 2 * y_0 + y_p1
            return 0.5 * (y_m1 - y_p1) / denom if denom != 0 else 0.0
        return 0.0

    # --------------------------------------------------
    # YIN pipeline
    # --------------------------------------------------

    def _getPitchYIN(self):
        asmdf = self._fft_asmdf(self.buffer)
        cmnd  = self._cmndf(asmdf)

        lag_min = max(2, round(self.sampleRate / self.f_max))
        lag_max = min(len(cmnd), round(self.sampleRate / self.f_min))

        lag          = self._absoluteThreshold(cmnd, lag_min, lag_max)
        refined_lag  = self._parabolicInterpYIN(asmdf, lag)

        if refined_lag < 1:
            return None
        return self.sampleRate / refined_lag

    def _fft_asmdf(self, samps):
        """ASMDF via FFT using ASMDF(lag) = 2*(ACF(0) - ACF(lag))."""
        acf = self._fft_acf(samps)
        return 2 * (acf[0] - acf)

    def _cmndf(self, asmdf):
        """Cumulative Mean Normalized Difference — removes short-lag bias."""
        norm = np.zeros(len(asmdf))
        norm[0] = 1
        cumsum = np.cumsum(asmdf[1:])
        with np.errstate(divide='ignore', invalid='ignore'):
            norm[1:] = np.where(
                cumsum > 0,
                asmdf[1:] * np.arange(1, len(asmdf)) / cumsum,
                1
            )
        return norm

    def _absoluteThreshold(self, cmnd, lag_min, lag_max):
        """
        Find the first lag below yinThreshold, then walk to the dip bottom.
        Falls back to the global minimum if no lag clears the threshold.
        """
        for lag in range(lag_min, lag_max):
            if cmnd[lag] < self.yinThreshold:
                while lag + 1 < lag_max and cmnd[lag + 1] < cmnd[lag]:
                    lag += 1
                return lag
        return int(np.argmin(cmnd[lag_min:lag_max]) + lag_min)

    def _parabolicInterpYIN(self, asmdf, lag):
        """Refine lag on the raw ASMDF curve."""
        if lag <= 0 or lag >= len(asmdf) - 1:
            return float(lag)
        denom = asmdf[lag - 1] - 2 * asmdf[lag] + asmdf[lag + 1]
        if denom == 0:
            return float(lag)
        return lag + 0.5 * (asmdf[lag - 1] - asmdf[lag + 1]) / denom

    # --------------------------------------------------
    # Shared helpers
    # --------------------------------------------------

    def _findLocalMaxima(self, x):
        return [
            i for i in range(1, len(x) - 1)
            if x[i] > x[i - 1] and x[i] > x[i + 1]
        ]

    def getCentsError(self, fn, freqCalc):
        if freqCalc is None or freqCalc <= 0:
            return None
        return 1200 * np.log2(freqCalc / fn)

    def get_DBSPL(self):
        if self.buffer is None:
            return -np.inf
        rms = np.sqrt(np.mean(self.buffer ** 2))
        if rms == 0:
            return -np.inf
        return 20 * np.log10(rms / 0.00002)