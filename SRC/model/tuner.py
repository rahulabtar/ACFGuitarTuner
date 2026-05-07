from pitcher import Pitcher, PitchMethod
from audio_in import Audio_In


class Tuner:
    def __init__(self, audio_in: Audio_In, pitcher: Pitcher):
        self.audio_in       = audio_in
        self.pitcher        = pitcher
        self.buffer_size    = None
        self.detection_method = None
        self.detected_freq  = None

    def setBufferSize(self, size):
        self.buffer_size = size
        self.pitcher.setBufferSize(size)

    def setSampleRate(self, rate):
        self.pitcher.setSampleRate(rate)
        self.audio_in.sample_rate = rate

    def setDetectionMethod(self, method: PitchMethod):
        self.detection_method = method
        self.pitcher.setMethod(method)

    def update(self):
        block = self.audio_in.buffer
        if block is None:
            return None
        self.pitcher.loadBuffer(block)
        self.detected_freq = self.pitcher.getPitch()
        return self.detected_freq