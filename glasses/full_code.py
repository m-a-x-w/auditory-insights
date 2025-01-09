import sounddevice as sd
import librosa
import numpy as np
import torch
from panns_inference import AudioTagging, labels
from scipy.io import wavfile
import noisereduce as nr
import time
import os
import math
import sys
import os

if os.path.exists('/lib'):
    sys.path.append('lib')

import RPi.GPIO as GPIO
import time
import logging    
from waveshare_OLED import OLED_1in51
from PIL import Image, ImageDraw, ImageFont

SIREN_INDEXES = {322, 323, 324, 325, 396, 397}

class AudioTagger:
    def __init__(self, checkpoint_path, device='cpu'):
        self.device = device
        self.model = AudioTagging(checkpoint_path=checkpoint_path, device=device)

    def record_audio(self, duration, sample_rate, output_file, gain=1.0, target_rate=32000):
        audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
        sd.wait()
        audio = audio.squeeze()
        
        wavfile.write(output_file, sample_rate, (audio * 32767).astype('int16'))

        amplified_audio = audio * gain

        if sample_rate != target_rate:
            amplified_audio = librosa.resample(amplified_audio, orig_sr=sample_rate, target_sr=target_rate)

        return amplified_audio

    def noise_reduction(self, input_file, output_file):
        sample_rate, audio = wavfile.read(input_file)

        reduced_audio = nr.reduce_noise(y=audio, sr=sample_rate)

        wavfile.write(output_file, sample_rate, reduced_audio)

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
    for k in SIREN_INDEXES:
        print('{}: {:.3f}'.format(np.array(labels)[k], clipwise_output[k]), end=' | ')
    print()

def check_audio_for_siren(clipwise_output, z=5):
    sorted_indexes = np.argsort(clipwise_output)[::-1]
    for k in SIREN_INDEXES:
        if clipwise_output[k] > 0.1:
            return True
    return False

LEFT_MIC_PIN = 6
MIDDLE_MIC_PIN = 24
RIGHT_MIC_PIN = 26

DETECTION_DELAY = 0.005  

GPIO.setmode(GPIO.BCM)
GPIO.setup(LEFT_MIC_PIN, GPIO.IN)
GPIO.setup(MIDDLE_MIC_PIN, GPIO.IN)
GPIO.setup(RIGHT_MIC_PIN, GPIO.IN)

class Display():
    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)
        
        self.display = OLED_1in51.OLED_1in51()
        self.display.Init()
        self.display.clear()
        self.image = Image.new('1', (self.display.width, self.display.height), "WHITE")
        
        self.buf = None
        
        logging.info("Initialized OLED Display")
    
    def clear(self):
        self.image = Image.new('1', (self.display.width, self.display.height), "WHITE")
        self.display.clear()

    def writeImage(self, imagePath, loc, rotation):
        img = Image.new('1', (self.display.width, self.display.height), 255)
        imgIn = Image.open(imagePath)
        
        img.paste(imgIn, loc)
        img = img.rotate(rotation)
        self.display.ShowImage(self.display.getbuffer(img))
        
        logging.debug(f"Wrote image using imagepath: {imagePath} with rotation: {rotation}")
        
    def draw_line(self, angle):
        image1 = Image.new('1', (self.display.width, self.display.height), "WHITE")
        draw = ImageDraw.Draw(image1)
        length = min(self.display.width, self.display.height) // 2
        center = (self.display.width // 2, self.display.height // 2)
        end_point = (
            center[0] + 12 * math.cos(math.radians(angle)),  
            center[1] + 12 * math.sin(math.radians(angle)),
        )

        draw.line([center, end_point], fill=0)

        self.display.ShowImage(self.display.getbuffer(image1))
        logging.debug(f"Drew line with angle: {angle}")
        
    def draw_line_with_indicator(self, angle):
        draw = ImageDraw.Draw(self.image)
        length = max(self.display.width, self.display.height)
        center = (self.display.width // 2, self.display.height // 2)
        end_point = (
            center[0] + length * math.cos(math.radians(angle)),
            center[1] + length * math.sin(math.radians(angle)),
        )

        draw.line([center, end_point], fill=0)

        draw.ellipse([(end_point[0]-2, end_point[1]-2), (end_point[0]+2, end_point[1]+2)], fill="RED")

        self.display.ShowImage(self.display.getbuffer(self.image))
        logging.debug(f"Drew line with angle: {angle}")
        
    def draw_arrow(self):
        draw = ImageDraw.Draw(self.image)
        center = (self.display.width // 2 - 10, self.display.height // 2)
        arrow_length = 20 
        arrow_width = 10 

        arrow_points = [
            (center[0], center[1] - arrow_width // 2),
            (center[0], center[1] + arrow_width // 2),
            (center[0] + arrow_length, center[1]) 
        ]

        draw.polygon(arrow_points, fill=0)

        self.display.ShowImage(self.display.getbuffer(self.image))
        logging.debug("Drew arrow")

d = Display()

timestamps = []
angles = []
left_timestamp = 0
middle_timestamp = 0
right_timestamp = 0        

LEFT_ANGLE = 110
MIDDLE_ANGLE = 40
RIGHT_ANGLE = 250

def detect_sound(pin):
    global left_timestamp, middle_timestamp, right_timestamp, timestamps, angles

    current_timestamp = time.time()

    if pin == LEFT_MIC_PIN:
        left_timestamp = current_timestamp
    elif pin == MIDDLE_MIC_PIN:
        middle_timestamp = current_timestamp
    elif pin == RIGHT_MIC_PIN:
        right_timestamp = current_timestamp

    if (
        left_timestamp > middle_timestamp - DETECTION_DELAY
        and right_timestamp > middle_timestamp - DETECTION_DELAY
        and abs(left_timestamp - right_timestamp) <= DETECTION_DELAY
    ):
        timestamps.append(middle_timestamp)
        angles.append((LEFT_ANGLE+RIGHT_ANGLE) / 2)
    elif (
        left_timestamp > right_timestamp - DETECTION_DELAY
        and middle_timestamp > right_timestamp - DETECTION_DELAY
        and abs(left_timestamp - middle_timestamp) <= DETECTION_DELAY
    ):
        timestamps.append(right_timestamp)
        angles.append((LEFT_ANGLE + MIDDLE_ANGLE)/2) 
    elif (
        middle_timestamp > left_timestamp - DETECTION_DELAY
        and right_timestamp > left_timestamp - DETECTION_DELAY
        and abs(middle_timestamp - right_timestamp) <= DETECTION_DELAY
    ):
        timestamps.append(left_timestamp)
        angles.append((RIGHT_ANGLE + MIDDLE_ANGLE)/2) 
    else:
        if left_timestamp > middle_timestamp + DETECTION_DELAY and left_timestamp > right_timestamp + DETECTION_DELAY:
            timestamps.append(left_timestamp)
            angles.append(LEFT_ANGLE)
        elif middle_timestamp > left_timestamp + DETECTION_DELAY and middle_timestamp > right_timestamp + DETECTION_DELAY:
            timestamps.append(middle_timestamp)
            angles.append(MIDDLE_ANGLE)
        elif right_timestamp > left_timestamp + DETECTION_DELAY and right_timestamp > middle_timestamp + DETECTION_DELAY:
            timestamps.append(right_timestamp)
            angles.append(RIGHT_ANGLE)

GPIO.add_event_detect(LEFT_MIC_PIN, GPIO.RISING, callback=detect_sound)
GPIO.add_event_detect(MIDDLE_MIC_PIN, GPIO.RISING, callback=detect_sound)
GPIO.add_event_detect(RIGHT_MIC_PIN, GPIO.RISING, callback=detect_sound)

def circular_mean(angles):
    sum_sin = sum(math.sin(math.radians(angle)) for angle in angles)
    sum_cos = sum(math.cos(math.radians(angle)) for angle in angles)

    mean_angle = math.degrees(math.atan2(sum_sin, sum_cos))
    mean_angle = (mean_angle + 360) % 360 

    return mean_angle



if __name__ == '__main__':
    duration = 1
    sample_rate = 44100
    gain_factor = 5.0
    output_dir = "recordings/" 
    checkpoint_path = None

    os.makedirs(output_dir, exist_ok=True)

    tagger = AudioTagger(checkpoint_path)
    
    try:
        while True:
            timestamp = int(time.time())
            output_file = os.path.join(output_dir, f"recording_{timestamp}.wav")

            recorded_audio = tagger.record_audio(duration, sample_rate, output_file, gain=gain_factor)
            print(f"Audio saved to {output_file}")
            d.clear()
            d.draw_arrow()

            if len(timestamps) < 20:
                print("Not enough sound detected")
                timestamps = []
                angles = []
                continue
            

            clipwise_output, _ = tagger.infer(recorded_audio)
            #print_audio_tagging_result(clipwise_output[0])

            contains_siren = check_audio_for_siren(clipwise_output[0])
            if contains_siren:
                print("Siren detected in the audio.")

                avg_angle = circular_mean(angles)
                d.draw_line_with_indicator(avg_angle)
            else:
                print("No siren detected in the audio.")

            timestamps = []
            angles = []
    except KeyboardInterrupt:
        print("Script terminated by user.")
    finally:
        GPIO.cleanup()
