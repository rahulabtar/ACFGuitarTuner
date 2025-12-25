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

import time
import numpy as np

# assume Pitcher + PitchMethod already imported
# assume Audio_In already imported


if __name__ == "__main__":
    # -------------------------------
    # User configuration
    # -------------------------------
    PITCH_BUFFER_SIZE = 2048
    F_MIN = 50.0
    F_MAX = 500.0

    audio_in = Audio_In()

    # -------------------------------
    # List input devices
    # -------------------------------
    inputs = audio_in.get_inputs()
    print("Available Input Devices:")
    for i, dev in enumerate(inputs):
        print(f"{i}: {dev['name']} - Channels: {dev['max_input_channels']}")

    device_index = int(input("Enter device index: "))
    channel_index = int(input("Enter channel number (1-based): ")) - 1
    sample_rate = int(input("Enter sampling rate (e.g., 44100): "))
    block_size = int(input("Enter block size (e.g., 512): "))

    # -------------------------------
    # Initialize audio stream
    # -------------------------------
    audio_in.reincarnate_stream(
        device=device_index,
        sample_rate=sample_rate,
        channel=channel_index,
        buffer_size=block_size
    )

    audio_in.start_stream()
    print("Audio stream started. Press Ctrl+C to stop.")

    # -------------------------------
    # Initialize Pitcher
    # -------------------------------
    pitcher = Pitcher()
    pitcher.setSampleRate(sample_rate)
    pitcher.setBufferSize(PITCH_BUFFER_SIZE)
    pitcher.setMethod(PitchMethod.ACF)

    # Optional: tighten pitch range for guitar
    pitcher.f_min = F_MIN
    pitcher.f_max = F_MAX

    # Initialize circular buffer
    pitcher.buffer = np.zeros(PITCH_BUFFER_SIZE)

    # -------------------------------
    # Main processing loop
    # -------------------------------
    try:
        while True:
            time.sleep(0.05)  # ~20 Hz pitch updates

            block = audio_in.buffer
            if block is None:
                continue

            block = np.asarray(audio_in.buffer).reshape(-1)

            # Feed new audio into Pitcher
            pitcher.loadBuffer(block)

            pitch = pitcher.getPitch()
            db_spl = pitcher.get_DBSPL()

            if pitch is not None and db_spl is not None:
                print(f"Pitch: {pitch:7.2f} Hz | Level: {db_spl:6.1f} dB SPL")
            else:
                print("Waiting for stable signal...")

    except KeyboardInterrupt:
        print("\nStopping audio stream...")
        audio_in.end_stream()


    

    

