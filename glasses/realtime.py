import librosa
import numpy as np
import sounddevice as sd
from panns_inference import AudioTagging, labels
import torch
from scipy.io import wavfile  
SIREN_INDEXES = {322, 323, 324, 325, 396, 397}

class AudioTagger:
    def __init__(self, checkpoint_path, device='cpu'):
        self.device = device
        self.model = AudioTagging(checkpoint_path=checkpoint_path, device=device)

    def record_audio(self, duration, samplerate, target_rate, device_id=None, gain=1.0, output_file=None):
        audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, device=device_id, dtype='float32')
        sd.wait()  
        audio = audio.squeeze() 
        amplified_audio = audio * gain

        if samplerate != target_rate:
            amplified_audio = librosa.resample(amplified_audio, orig_sr=samplerate, target_sr=target_rate)

        if output_file:
            wavfile.write(output_file, target_rate, amplified_audio.astype(np.int16))

        return amplified_audio

    def infer(self, audio):
        audio = torch.FloatTensor(audio) / np.iinfo(np.int16).max
        audio = audio.unsqueeze(0)

        with torch.no_grad():
            (clipwise_output, embedding) = self.model.inference(audio)
        return clipwise_output, embedding

def print_audio_tagging_result(clipwise_output):
    sorted_indexes = np.argsort(clipwise_output)[::-1]
    for k in range(5):
        print('{}: {:.3f}'.format(np.array(labels)[sorted_indexes[k]], clipwise_output[sorted_indexes[k]]), end=' | ')
    print()

def check_audio_for_siren(clipwise_output, z=5):
    sorted_indexes = np.argsort(clipwise_output)[::-1]
    for k in range(z):
        if (sorted_indexes[k]) in SIREN_INDEXES:
            return True
    return False

def list_audio_devices():
    print("Available audio devices:")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"ID: {i}, Name: {device['name']}")

if __name__ == '__main__':
    list_audio_devices()
    device_id = int(input("Mic ID: "))
    native_samplerate = 48000  
    gain_factor = 1.0 

    tagger = AudioTagger(None)

    i = 0
    while True:
        audio = tagger.record_audio(duration=1, samplerate=native_samplerate, target_rate=32000, gain=gain_factor, device_id=device_id, output_file=f"sounds/{i}.wav")
        clipwise_output, _ = tagger.infer(audio)
        print_audio_tagging_result(clipwise_output[0])
        i+=1

