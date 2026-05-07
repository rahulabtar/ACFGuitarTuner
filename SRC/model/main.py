import time
import numpy as np
from pitcher import Pitcher, PitchMethod
from audio_in import Audio_In
from tuner import Tuner

COMMON_SAMPLE_RATES = [8000, 11025, 16000, 22050, 44100, 48000, 88200, 96000, 192000]
PITCH_BUFFER_SIZE   = 2048
F_MIN               = 50.0
F_MAX               = 500.0


# --------------------------------------------------
# Device probing
# --------------------------------------------------

import sounddevice as sd

def probe_supported_rates(device_index: int, num_channels: int) -> list[int]:
    supported = []
    for rate in COMMON_SAMPLE_RATES:
        try:
            sd.check_input_settings(
                device=device_index,
                channels=num_channels,
                samplerate=rate
            )
            supported.append(rate)
        except sd.PortAudioError:
            pass
    return supported


# --------------------------------------------------
# Setup wizard
# --------------------------------------------------

def select_device(inputs: list[dict]) -> tuple[int, dict]:
    print("\n--- Available input devices ---")
    for i, dev in enumerate(inputs):
        print(f"  {i}: {dev['name']}")
    index = int(input("\nSelect device index: "))
    return index, inputs[index]


def select_channels(device: dict) -> int:
    max_ch = device['max_input_channels']
    print(f"\n--- Channels (1 – {max_ch}) ---")
    for i in range(1, max_ch + 1):
        print(f"  {i - 1}: {i} channel{'s' if i > 1 else ''}")
    choice = int(input("Select channel option index: "))
    return choice + 1


def select_sample_rate(device_index: int, max_channels: int, device: dict) -> int:
    print("\nProbing supported sample rates...")
    rates = probe_supported_rates(device_index, max_channels)

    if not rates:
        fallback = int(device.get('default_sample_rate', 44100))
        print(f"No standard rates detected — using device default ({fallback} Hz).")
        return fallback

    default_rate = int(device.get('default_sample_rate', 0))
    print("\n--- Supported sample rates ---")
    for i, rate in enumerate(rates):
        marker = " (default)" if rate == default_rate else ""
        print(f"  {i}: {rate} Hz{marker}")

    choice = int(input("Select sample rate index: "))
    return rates[choice]


def select_block_size() -> int:
    print("\n--- Block size ---")
    options = [256, 512, 1024, 2048]
    for i, size in enumerate(options):
        print(f"  {i}: {size}")
    choice = int(input("Select block size index (or enter a custom value directly): "))
    if 0 <= choice < len(options):
        return options[choice]
    return choice     # treat out-of-range input as a raw sample count


def select_pitch_method() -> PitchMethod:
    methods = [PitchMethod.ACF, PitchMethod.YIN]
    print("\n--- Pitch detection method ---")
    for i, m in enumerate(methods):
        print(f"  {i}: {m.name}")
    choice = int(input("Select method index: "))
    return methods[choice]


# --------------------------------------------------
# Entry point
# --------------------------------------------------

if __name__ == "__main__":

    audio_in = Audio_In()
    inputs   = audio_in.get_inputs()

    # --- Setup wizard ---
    device_index, device = select_device(inputs)
    num_channels         = select_channels(device)
    sample_rate          = select_sample_rate(device_index, num_channels, device)
    block_size           = select_block_size()
    pitch_method         = select_pitch_method()

    print(f"""
--- Session configuration ---
  Device      : {device['name']}
  Channels    : {num_channels}
  Sample rate : {sample_rate} Hz
  Block size  : {block_size}
  Method      : {pitch_method.name}
  Pitch range : {F_MIN} – {F_MAX} Hz
  Buffer size : {PITCH_BUFFER_SIZE} samples
""")

    # --- Audio stream ---
    audio_in.reincarnate_stream(
        device=device_index,
        sample_rate=sample_rate,
        channel=0,              # always read channel 0; num_channels controls stream width
        buffer_size=block_size
    )
    audio_in.start_stream()
    print("Audio stream started. Press Ctrl+C to stop.\n")

    # --- Tuner ---
    pitcher = Pitcher()
    pitcher.setFrequencyRange(F_MIN, F_MAX)

    tuner = Tuner(audio_in, pitcher)
    tuner.setBufferSize(PITCH_BUFFER_SIZE)
    tuner.setSampleRate(sample_rate)
    tuner.setDetectionMethod(pitch_method)

    # --- Main loop ---
    try:
        while True:
            time.sleep(0.05)

            pitch  = tuner.update()
            db_spl = tuner.pitcher.get_DBSPL()

            if pitch is not None:
                print(f"Pitch: {pitch:7.2f} Hz | Level: {db_spl:6.1f} dB SPL")
            else:
                print("Waiting for stable signal...")

    except KeyboardInterrupt:
        print("\nStopping...")
        audio_in.end_stream()