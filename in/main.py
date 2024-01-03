#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
import os

if os.path.exists('/lib'):
    sys.path.append('lib')

import logging    
import time
import traceback
from waveshare_OLED import OLED_1in51
from PIL import Image,ImageDraw,ImageFont
from time import sleep
import RPi.GPIO as GPIO
import threading


GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.IN)
GPIO.setup(24, GPIO.IN)

class Display():
  def __init__(self):
    logging.basicConfig(level=logging.DEBUG)
    
    self.display = OLED_1in51.OLED_1in51()
    self.display.Init()
    self.display.clear()
    
    self.buf = None
    
    logging.info("Initialized OLED Display")
  
  def clear(self):
    self.display.clear()

  def writeImage(self, imagePath, loc):
    img = Image.new('1', (self.display.width, self.display.height), 255)
    imgIn = Image.open(imagePath)
    
    img.paste(imgIn, loc)
    self.display.ShowImage(self.display.getbuffer(img))
    
    logging.debug(f"Wrote image using imagepath: {imagePath} at loc: {loc}")
    
d = Display()

lock = threading.Lock()

def soundEvent(num):
    with lock:
        print(num)
        
        if num == 26:
            d.writeImage("leftArrow.bmp", (0, 0))
        else:
            d.writeImage("rightArrow.bmp", (0, 0))

        d.clear()

        active = False

GPIO.add_event_detect(26, GPIO.RISING, callback=lambda x: soundEvent(26), bouncetime=50)
GPIO.add_event_detect(24, GPIO.RISING, callback=lambda x: soundEvent(24), bouncetime=50)


while True:
    print("Running...")
    time.sleep(1)

class Microphone:
    def __init__(self, num, pin):
        self.num = num
        self.pin = pin

        GPIO.add_event_detect(self.pin, GPIO.RISING, callback=self.onEvent, bouncetime=100)

    def onEvent(self):
        pass