#!/usr/bin/python
from imutils.video.pivideostream import PiVideoStream
import numpy
import math
import time
import cv2
import smbus
import serial
import serial.tools.list_ports as lp
import argparse

# -----------------------------------------------------------------------
# modify globals to tailor to different setups
# -----------------------------------------------------------------------

address = 0x08 # address of the Arduino
arduinoSerialName = "ACM"

gassianBlurAmount = 11
accumulateWeight = 0.5
acceptableDelta = 7
dilateIterations = 2

minArea = 500
maxArea = 9000

xJitterAmount = 8
yJitterAmount = 6

# -----------------------------------------------------------------------
# other variables to set up the rest of the code
# -----------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument("--debug", help="this will print out status messages", action="store_true")
args = parser.parse_args()
debugMode = args.debug

bus = smbus.SMBus(1)

vs = PiVideoStream().start() # starting our video stream
time.sleep(1)

averageImage = None # average frame data
mode = 0 # default mode for the turret
ser = None # serial object
threat = 0 # default threat of 0
lastX = 0
lastW = 0
lastY = 0
lastH = 0
written = False
changed = True

# -----------------------------------------------------------------------
# communicate with the Pi through i2c
# mode 0 for coordinate sending, mode 1 to disable turret
# threat 0 laser is off, threat 1 laser is on
# -----------------------------------------------------------------------
def sendToArduino(mode, threat, x_coord, y_coord):
  global written
  try: # try block to catch i2c errors without aborting code
    if mode is 0:
      written = False
      data = [threat]
      # turn numbers into strings
      for n in str(x_coord):
        data.append(ord(n))
      # send each char byte to arduino
      bus.write_i2c_block_data(address, 0, data)
      data = [threat]
      for n in str(y_coord):
        data.append(ord(n))
      bus.write_i2c_block_data(address, 1, data)
      data = [threat]
      if debugMode:
        print("[NOTE] Writing x: {0}, y: {1}".format(x_coord, y_coord))
    elif mode is 1:
      if not written:
        bus.write_i2c_block_data(address, 2, [threat])
        if debugMode:
          print("[NOTE] Turret disabled")
        written = True
  except IOError:
    if debugMode:
      print("[NOTE] i2c error")
    pass

# -----------------------------------------------------------------------
# monitor serial input and update state if there are any changes
# -----------------------------------------------------------------------
def readSerial():
  try:
    # global variables
    global mode
    global threat
    global ser
    global written
    ser.write(str(1))
    if ser.in_waiting:
      written = False
      mode_and_threat = int(ser.readline())
      threat = mode_and_threat % 10
      mode = int(math.floor(mode_and_threat / 10)) % 10
      if debugMode:
        print("[NOTE] Mode updated to {0}".format(mode))
        print("[NOTE] Threat updated to {0}".format(threat))
      # reset laser pointer
      if mode is 1:
        sendToArduino(mode, threat, None, None)
  except IOError:
    if debugMode:
      print("[NOTE] Serial error")
    ser = None
    pass

# -----------------------------------------------------------------------
# the code starts at this point; follow each step line by line
# -----------------------------------------------------------------------
while True:
  # establish serial communication before system starts or if it gets lost
  if ser is None:
    arduinoPorts = [p.device for p in lp.comports() if arduinoSerialName in p.description]
    try:
      ser = serial.Serial(arduinoPorts[0], 9600, timeout=0)
      # wait for the Arduino to power up
      time.sleep(4)
    except:
      if debugMode:
        print("[NOTE] Serial error")
      pass
  else:
    readSerial()

  # grab a frame from our threaded pivideostream
  f = vs.read()

  # convert the frame to grayscale
  gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
  gray = cv2.GaussianBlur(gray, (gassianBlurAmount, gassianBlurAmount), 0)

  # initiate the average
  if averageImage is None:
    averageImage = numpy.float32(gray)
    continue

  # turn our average image into something usable 
  frameComp = cv2.convertScaleAbs(averageImage)

  # calculate the difference in the frame and average image
  frameDelta = cv2.absdiff(frameComp, gray)

  # add our frame to the running average
  cv2.accumulateWeighted(gray, averageImage, accumulateWeight)

  # find the areas that are above our threshold 
  threshold = cv2.threshold(frameDelta, acceptableDelta, 255, cv2.THRESH_BINARY)[1]

  # fill in the holes and find the contours
  threshold = cv2.dilate(threshold, None, iterations=dilateIterations)
  contours = cv2.findContours(threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]

  # find the biggest contour within our range
  temp = None
  for c in contours:
    if cv2.contourArea(c) < minArea or cv2.contourArea(c) > maxArea:
      continue
    elif temp is None or cv2.contourArea(c) > cv2.contourArea(temp):
      temp = c

  # draw boxes around our area of interest, taking into account our jitter reduction
  if temp is not None:
    (x, y, w, h) = cv2.boundingRect(temp)
    if abs(lastX - (x + w/2)) > lastW/xJitterAmount:
      lastX = int(x + w/2)
      lastW = w
      changed = True
    if abs(lastY - (y + h/3)) > lastH/yJitterAmount:
      lastY = int(y + h/3)
      lastH = h
      changed = True
    if debugMode:
      cv2.rectangle(f, (x, y), (x + w, y + h), (0, 255, 0), 1)
    if changed:
      sendToArduino(mode, threat, lastX, lastY)
      changed = False

  # draw things for our debug mode
  if debugMode:
    cv2.circle(f, (lastX, lastY), 3, (0, 255, 0), 2)
    cv2.imshow("Frames", f)
    cv2.imshow("Thresh", threshold)
    cv2.imshow("frame delta", frameDelta)
    cv2.imshow("avg", frameComp)
    cv2.waitKey(1)
