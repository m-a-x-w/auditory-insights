import os
import matplotlib.pyplot as plt
import numpy as np
import librosa
import sounddevice as sd  # Import the sounddevice library
import panns_inference
from panns_inference import AudioTagging, SoundEventDetection, labels
import torch
import torch.nn.functional as F
def print_audio_tagging_result(clipwise_output):
    """Visualization of audio tagging result.

    Args:
      clipwise_output: (classes_num,)
    """
    sorted_indexes = np.argsort(clipwise_output)[::-1]

    # Print audio tagging top probabilities
    for k in range(10):
        print('{}: {:.3f}'.format(np.array(labels)[sorted_indexes[k]], 
            clipwise_output[sorted_indexes[k]]))



if __name__ == '__main__':
    device = 'cpu'  # 'cuda' | 'cpu'

    print('------ Audio tagging ------')
    at = AudioTagging(checkpoint_path=None, device=device)

    # Record microphone input
    duration = 2  # Set the duration for recording in seconds
    audio = sd.rec(int(duration * 32000), samplerate=32000, channels=1, dtype='float32')
    sd.wait()

    audio = torch.from_numpy(audio)

    # Extract spectrogram
    spec_extractor = at.model.spectrogram_extractor
    audio_input = spec_extractor(audio)  # Adjust the input shape

    # Adjust padding size based on the input shape
    pad_size = (audio_input.shape[-1] // 2, audio_input.shape[-1] // 2)
    x = F.pad(audio_input, pad=(0, 0, pad_size[0], pad_size[1]), mode='constant', value=0)

    x = x.unsqueeze(0)  # Add batch dimension
    x = x.to(device)

    (clipwise_output, embedding) = at.inference(x)
    print_audio_tagging_result(clipwise_output[0])
