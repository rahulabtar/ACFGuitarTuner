
import numpy as np
import enum

class PitchMethod(enum.Enum):
    ACF = 1
    AMDF = 2
    YIN = 3

class Pitcher:
    def __init__(self):
        self.buffer = None
        self.sampleRate = None

    def setBuffer(self, buffer):
        self.buffer = buffer
    
    def setSampleRate(self, sampleRate):
        self.sampleRate = sampleRate

    def getPitchACF(self):
        # Placeholder for ACF pitch detection implementation
        corrs = self._getCorr(self.buffer)
        maxima = self.findLocalMaxima(corrs)
        if (len(maxima) < 2): print("Print, Warning Not enough maxima found, expand ACF search range")
        return self.sampleRate / (maxima[1])

    def _ACF(self, buffer, lag):
        R = 0 
        if lag == 0:
            R = np.sum(buffer * buffer) 
        else:
            R = np.sum(buffer[:-lag] * buffer[lag:])
        return R

    def _getCorr(self, samps):
        corrs = []
        # for lag in range(round(fs / fHigh) - 1, round(fs / fLow)):
        for lag in range(0, len(samps)):
            corrs.append((self._ACF(samps, lag))) 
        return corrs

    def _findLocalMaximaInter(self, corrs):
        maxima = self.findLocalMaxima(corrs)
        return maxima + (0.5) * ((corrs[maxima - 1]) - corrs[maxima + 1]) / (corrs[maxima - 1] - 2 * corrs[maxima] + corrs[maxima + 1])

    def getCentsError(fn, freqCalc):
        """Calculate the error in cents between two given frequencies."""
        try:
            val = 1200 * np.log2(freqCalc/fn)
        except:
            val = "/0 error"
        finally:
            return val


if __name__ == "__main__":
    pitcher = Pitcher(44100)
    # Example usage
    buffer = np.random.rand(1024)  # Replace with actual audio buffer
    pitcher.setBuffer(buffer)
    pitcher.setSampleRate(44100)
    pitch = pitcher.getPitchACF()
    print(f"Detected Pitch: {pitch} Hz")