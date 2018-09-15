#!/usr/bin/python

from settings import SERIAL_PORT, SERVER_URL_BASE, PRINTER_SECRET
import socket
import os
import urllib
import cStringIO
import json
import datetime
import requests
import polling
import inkyphat
from PIL import Image, ImageFont
from Adafruit_Thermal import *

inkyphat.set_colour("black")

DIRNAME = os.path.dirname(__file__)
LOGO_IMAGE = Image.open(os.path.join(DIRNAME, "selfieboxlogo.png"))
FONT_MEDIUM = ImageFont.truetype(
  os.path.join(DIRNAME, "fonts/Source Code Pro_500.ttf"),
  20
)
FONT_BOLD = ImageFont.truetype(
  os.path.join(DIRNAME, "fonts/Source Code Pro_600.ttf"), 
  75
)

printer = Adafruit_Thermal(SERIAL_PORT, 19200, timeout=5)

def get_ip():
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  try:
    # doesn't even have to be reachable
    s.connect(('10.255.255.255', 1))
    IP = s.getsockname()[0]
  except:
    IP = '127.0.0.1'
  finally:
    s.close()
  return IP

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


def check_for_new_prints():
  currentCode = requests.get(SERVER_URL_BASE + "/code?secret=" + PRINTER_SECRET).text
  print "Updating code to " + currentCode
  update_code_on_screen(currentCode)
  print "Code updated "

  requests.post(SERVER_URL_BASE + "/printed?code=" + currentCode)

  def is_correct_code(response):
    print "status_code = " + str(response.status_code)
    return response.status_code == 200

  print "Polling to check code is correct"
  response = polling.poll(
      lambda: requests.get(SERVER_URL_BASE + "/data?code=" + currentCode),
      check_success=is_correct_code,
      step=5,
      poll_forever=True)

  data = response.json()
  print data

  requests.post(SERVER_URL_BASE + "/printing?code=" + currentCode)
  print "Printing image..."
  update_text_on_screen('Printing...')

  file = cStringIO.StringIO(requests.get(SERVER_URL_BASE + "/image?code=" + currentCode).content)
  image = Image.open(file)

  printer.printImage(LOGO_IMAGE, True)
  printer.feed(1)

  printer.justify('C')

  printer.println(datetime.datetime.now().strftime("%d-%m-%Y %H:%M"))
  printer.feed(2)

  printer.justify('L')

  printer.printImage(image, True)
  printer.feed(1)

  printer.printBarcode("SLFEBOX", printer.CODE39)
  printer.feed(3)

  print "Printed..."
  requests.post(SERVER_URL_BASE + "/printed?code=" + currentCode)
  print "current code: " + currentCode
  requests.post(SERVER_URL_BASE + "/generateNewCode?code=" + currentCode)
  check_for_new_prints()

# send ip address to server
print "Send request to server for IP address"
serverURL = SERVER_URL_BASE + '/ip?address=' + get_ip() + '&secret=' + PRINTER_SECRET
requests.post(serverURL)

# set the screen to current datetime to show it's booted the script
print "Updating screen with current date"
update_text_on_screen(
  datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
)

# initial one to start us off
check_for_new_prints() 
