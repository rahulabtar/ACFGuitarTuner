import sounddevice as sd
import numpy as np
import time


class Audio_In():
    def __init__(self):
        """"Initialize Audio Input with default device and settings"""
        self.device = None #device of focus
        self.channel = None #channel of focus
        self.buffer = None
        self.stream = None

    def get_inputs(self):
        devices = sd.query_devices()
        input_devices = [dev for dev in devices if dev['max_input_channels'] > 0]
        return input_devices
    
    def set_input(self, device_num, channel_num):
        inputs = self.get_inputs()
        if device_num < 0 or device_num >= len(inputs):
            raise ValueError("Invalid device number")
        device = inputs[device_num]
        
        # Get device index instead of name
        device_index = device['index']
        max_channels = device['max_input_channels']

    def reincarnate_stream(self, device: int, sample_rate: int = 44100, channel: int = 1):
        """Recreate the stream with current device and channels"""
        # Stop existing stream if running
        if self.stream is not None and self.stream.active:
            self.stream.stop()
            self.stream.close()
            self.channel = channel
        
        # Recreate stream with current settings
        self.stream = sd.InputStream(
            device=self.device,
            channels=1, 
            samplerate=self.sample_rate,
            callback=self.audio_callback  # You'll need this
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
        
        # Handle any number of channels
        # Extract the channel we're interested in
        if indata.ndim == 1:
            # Single channel, already 1D
            channel_data = indata
        elif self.channels == 1:
            # We only recorded 1 channel
            channel_data = indata[:, 0]
        else:
            # Multiple channels recorded, extract the one we want
            channel_data = indata[:, self.selected_channel]
        
        # Store in buffer for processing
        self.buffer = channel_data

    def get_DBSPL(self):
        """Calculate and return the dB SPL of the current buffer"""
        if self.buffer is None:
            return None
        rms = np.sqrt(np.mean(self.buffer**2))
        db_spl = 20 * np.log10(rms / 0.00002)
        return db_spl

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
    audio_in.set_input(device_index, channel_index)

    #set the sampling rate as the user desires
    sample_rate = int(input("Enter sampling rate (e.g., 44100): "))

    #set the buffer size 
    buffer_size = int(input("Enter buffer size (e.g., 1024): "))


    audio_in.reincarnate_stream(device_index, sample_rate, channel_index)

    audio_in.start_stream()



    
    