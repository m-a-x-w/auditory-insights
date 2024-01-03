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
logging.basicConfig(level=logging.DEBUG)

try:
    disp = OLED_1in51.OLED_1in51()

    logging.info("\r1.51inch OLED ")
    disp.Init()
    logging.info("clear display")
    disp.clear()
    
    image1 = Image.new('1', (disp.width, disp.height), "WHITE")
    bmp = Image.open('pics/1.bmp')
    image1.paste(bmp, (0,0))

    disp.ShowImage(disp.getbuffer(image1.rotate(180)))
    time.sleep(3)
    
    
    disp.clear()

except IOError as e:
    logging.info(e)
    
except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    OLED_1in51.config.module_exit()
    exit()