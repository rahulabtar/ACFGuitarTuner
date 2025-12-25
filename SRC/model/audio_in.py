import sounddevice as sd
import numpy as np
import time

class Audio_In():
    def __init__(self):
        """"Initialize Audio Input with default device and settings"""
        self.channel = 0  # default to first channel
        self.buffer = None
        self.stream = None

    def get_inputs(self):
        devices = sd.query_devices()
        input_devices = [dev for dev in devices if dev['max_input_channels'] > 0]
        return input_devices
    
    def reincarnate_stream(self, device: int, sample_rate: int = 44100, channel: int = 0, buffer_size = 1024):
        """Recreate the stream with current device and channels"""
        # Stop existing stream if running
        if self.stream is not None and self.stream.active:
            self.stream.stop()
            self.stream.close()
        
        self.channel = channel
        device_info = self.get_inputs()[device]
        num_channels = device_info['max_input_channels']  # record all channels available
        
        # Recreate stream with all channels
        self.stream = sd.InputStream(
            device=device_info['index'],
            channels=num_channels,  # <- record all channels
            samplerate=sample_rate,
            blocksize=buffer_size,
            callback=self.audio_callback
        )

    def start_stream(self):
        """Start the audio stream"""
        if self.stream is not None:
            self.stream.start()
        else:
            raise RuntimeError("Stream is not initialized. Call reincarnate_stream first.")
    
    def end_stream(self):
        """End the audio stream"""
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def audio_callback(self, indata, frames, time, status):
        """Callback function to process incoming audio data"""
        if status:
            print(f"Audio callback status: {status}")
        
        # indata shape: (frames, channels)
        if indata.ndim == 1:
            self.buffer = indata
        else:
            # Safely extract the channel of interest
            if self.channel < indata.shape[1]:
                self.buffer = indata[:, self.channel]
            else:
                # fallback if requested channel is out of range
                self.buffer = indata[:, 0]




if __name__ == "__main__":
    audio_in = Audio_In()

    # get available inputs and print them
    inputs = audio_in.get_inputs()
    print("Available Input Devices:")
    for i, dev in enumerate(inputs):
        print(f"{i}: {dev['name']} - Channels: {dev['max_input_channels']}")

    # Now set the input as the user desires 
    device_index = int(input("Enter device index: "))
    avail_channels = inputs[device_index]['max_input_channels']
    print(f"Device supports {avail_channels} channels.")

    #set the chnnel as user desires
    channel_index = int(input("Enter channel number (1-based): "))

    #set the sampling rate as the user desires
    sample_rate = int(input("Enter sampling rate (e.g., 44100): "))

    #set the buffer size 
    buffer_size = int(input("Enter buffer size (e.g., 1024): "))

    audio_in.reincarnate_stream(device_index, sample_rate, channel_index, buffer_size)

    audio_in.start_stream()
    print("Audio stream started. Press Ctrl+C to stop.")
    
    for (i) in range(100):
        time.sleep(0.25)
        db_spl = audio_in.get_DBSPL()
        if db_spl is not None:
            print(f"Current dB SPL: {db_spl:.2f} dB")
        else:
            print("No audio data yet.")



    
    