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

LEFT_MIC_PIN = 26
MIDDLE_MIC_PIN = 24
RIGHT_MIC_PIN = 6

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
        
        logging.info("Initialized Display")
    
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

def circular_mean(angles):
    sum_sin = sum(math.sin(math.radians(angle)) for angle in angles)
    sum_cos = sum(math.cos(math.radians(angle)) for angle in angles)

    mean_angle = math.degrees(math.atan2(sum_sin, sum_cos))
    mean_angle = (mean_angle + 360) % 360 

    return mean_angle

while True:
    try:
        angles = [i for i in range(0, 181, 5)]
        for angle in angles:
            d.draw_arrow()
            d.draw_line_with_indicator(angle)
            time.sleep(0.5)
            d.clear()

        time.sleep(3)
        
        angles = [i for i in range(360, 181, -5)]
        for angle in angles:
            d.draw_arrow()
            d.draw_line_with_indicator(angle)
            time.sleep(0.5)
            d.clear()
    except KeyboardInterrupt:
        print("Script terminated by user.")
    finally:
        GPIO.cleanup()
