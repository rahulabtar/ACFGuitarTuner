from pitcher import Pitcher, PitchMethod
from audio_in import Audio_In

class Tuner():
    def __init__(self, AudioIn: Audio_In, Pitcher: Pitcher):
        self.bufferSize = None
        self.AudioIn = Audio_In
        self.Pitcher = Pitcher
        self.detectionMethod = None
        self.detected_freq = -1
    
    def setBufferSize(self, size):
        self.bufferSize = size

    def setSampleRate(self, rate):
        self.Pitcher.setSampleRate(rate)
        self.AudioIn.sample_rate = rate

    def setDetectionMethod(self, method: PitchMethod):
        self.detectionMethod = method

if __name__ == "__main__":
    tuner = Tuner(Audio_In(), Pitcher())
    tuner.setBufferSize(2048)
    print("Buffer Size set to:", tuner.bufferSize)
    tuner.setDetectionMethod(PitchMethod.ACF)
    print("Detection Method set to:", tuner.detectionMethod)
    tuner.setSampleRate(44100)
    print("Sample Rate set to:", tuner.Pitcher.sampleRate)

    

    

