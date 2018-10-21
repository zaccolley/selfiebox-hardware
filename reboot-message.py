#!/usr/bin/python

import socket
import os
import inkyphat
from PIL import ImageFont

inkyphat.set_colour("black")

DIRNAME = os.path.dirname(__file__)
FONT_MEDIUM = ImageFont.truetype(
  os.path.join(DIRNAME, "fonts/Source Code Pro_500.ttf"),
  20
)
FONT_BOLD = ImageFont.truetype(
  os.path.join(DIRNAME, "fonts/Source Code Pro_600.ttf"), 
  75
)

def update_screen(text, xOffset, yOffset, backgroundColor, foregroundColor, font):
  inkyphat.rectangle(
    (0, 0, inkyphat.WIDTH, inkyphat.HEIGHT),
    fill=backgroundColor,
    outline=backgroundColor
  )

  message = text
  w, h = font.getsize(message)
  x = (inkyphat.WIDTH / 2) - (w / 2) + xOffset
  y = (inkyphat.HEIGHT / 2) - (h / 2) + yOffset
  inkyphat.text((x, y), message, foregroundColor, font)

  inkyphat.show()

def update_text_on_screen(text):
  update_screen(text, 0, 0, inkyphat.BLACK, inkyphat.WHITE, FONT_MEDIUM)

def update_code_on_screen(code):
  update_screen(code, 0, -10, inkyphat.WHITE, inkyphat.BLACK, FONT_BOLD)


update_text_on_screen(
  'Rebooting...'
)