import sounddevice as sd

def list_audio_devices():
    print("Available audio devices:")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"ID: {i}, Name: {device['name']}")

list_audio_devices()

device_id = int(input("Select Device: "))



def test_sample_rates(device_id):
    for rate in [8000, 16000, 22050, 32000, 44100, 48000, 96000]:
        try:
            sd.check_input_settings(device=device_id, samplerate=rate)
            print(f"Sample rate {rate} Hz is supported.")
        except Exception as e:
            print(f"Sample rate {rate} Hz is not supported.")

test_sample_rates(device_id)
