#!/usr/bin/python

from settings import SERIAL_PORT, SERVER_URL_BASE, PRINTER_SECRET
import urllib
import cStringIO
import json
import datetime
import requests
import polling
import inkyphat
from PIL import Image, ImageFont
from Adafruit_Thermal import *

MAX_CHAR_LEN = 32

inkyphat.set_colour("black")
printer = Adafruit_Thermal(SERIAL_PORT, 19200, timeout=5)

def updateCode (code):
  inkyphat.rectangle((0, 0, inkyphat.WIDTH, inkyphat.HEIGHT), fill=inkyphat.BLACK, outline=inkyphat.BLACK)

  font = ImageFont.truetype("fonts/Source Code Pro_600.ttf", 80)

  message = code
  w, h = font.getsize(message)
  x = (inkyphat.WIDTH / 2) - (w / 2)
  y = (inkyphat.HEIGHT / 2) - (h / 2) - 10
  inkyphat.text((x, y), message, inkyphat.WHITE, font)

  inkyphat.show()

def print_with_padding(type, text):
  fillerCharsLen = MAX_CHAR_LEN - len(text)
  fillerChars = "." * fillerCharsLen

  if type == 'left':
    printer.println(text + fillerChars)
    return
  if type == 'right':
    printer.println(fillerChars + text)
    return
  
  printer.println(text)

def print_with_two_parts(leftText, rightText):
  if (len(leftText) + len(rightText)) < MAX_CHAR_LEN:
    fillerCharsLen = MAX_CHAR_LEN - len(leftText) - len(rightText)
    fillerChars = "." * fillerCharsLen
    printer.println(leftText + fillerChars + rightText)
  else:
    if len(leftText) > MAX_CHAR_LEN:
      printer.println(leftText)
    else:
      print_with_padding('left', leftText)

    if len(rightText) > MAX_CHAR_LEN:
      printer.println(rightText)
    else:
      print_with_padding('right', rightText)

def printCode(printer, code):
  printer.justify('R')
  printer.setSize('L')
  printer.println(code)
  printer.justify('L')
  printer.setSize('S')

def printMetaData(printer, data):
  printer.justify('C')
  printer.doubleHeightOn()
  if data["isDoNotTrackEnabled"] == True:
    printer.inverseOn()
    printer.println(' DO NOT TRACK: DISABLED ')
    printer.inverseOff()
  else:
    printer.println(' DO NOT TRACK: ENABLED ')
  printer.doubleHeightOff()
  printer.feed(1)

  printer.justify('L')

  if data["exif"]:
    printer.setSize('L')
    printer.println('Camera')
    printer.setSize('S')

    print_with_two_parts('Make', data["exif"]["make"])
    print_with_two_parts('Model', data["exif"]["model"])
    print_with_two_parts('Flash', data["exif"]["flash"])
    printer.feed(1)

  printer.setSize('M')
  printer.println('Device')
  printer.setSize('S')

  if data["browser"]:
    print_with_two_parts("Browser", data["browser"])

  if data["operatingSystem"]:
    print_with_two_parts("Operating System", data["operatingSystem"])

  if data["device"]:
    print_with_two_parts("Name", data["device"])

  if data["language"]:
    print_with_two_parts("Language", data["language"])

  if data["country"]:
    print_with_two_parts("Country", data["country"])

  if data["fingerprint"]["adblockEnabled"]:
    print_with_two_parts("AdBlock", "Enabled")
  else:
    print_with_two_parts("AdBlock", "Disabled")

  resolution = data["fingerprint"]["resolution"]
  print_with_two_parts("Screen", str(resolution[0]) + "x" + str(resolution[1]))

def checkForNewPrints():
  currentCode = requests.get(SERVER_URL_BASE + "/code?secret=" + PRINTER_SECRET).text
  print "Updating code to " + currentCode
  updateCode(currentCode)
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

  file = cStringIO.StringIO(requests.get(SERVER_URL_BASE + "/image?code=" + currentCode).content)
  # TODO: handle if this isnt a image
  image = Image.open(file)

  printCode(printer, data["code"])
  printer.feed(1)

  printer.println(datetime.datetime.now().isoformat())
  printer.feed(1)

  printer.printImage(image, True)
  printer.feed(1)

  if data["printMetaData"]:
    printMetaData(printer, data)
    printer.feed(1)

  printer.printBarcode("EMFCAMP", printer.CODE39)
  printer.setBarcodeHeight(100)
  printer.feed(4)

  print "Printed..."
  requests.post(SERVER_URL_BASE + "/printed?code=" + currentCode)
  print "current code: " + currentCode
  requests.post(SERVER_URL_BASE + "/generateNewCode?code=" + currentCode)
  checkForNewPrints()

checkForNewPrints() # initial one to start us off
