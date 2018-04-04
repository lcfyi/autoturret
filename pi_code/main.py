#!/usr/bin/python
from imutils.video.pivideostream import PiVideoStream
import numpy
import math
import time
import cv2
import smbus
import serial
import serial.tools.list_ports as lp

# -----------------------------------------------------------------------
# modify globals to tailor to different setups
# -----------------------------------------------------------------------

address = 0x08 # address of the Arduino
gassianBlurAmount = 11
accumulateWeight = 0.5
acceptableDelta = 7
dilateIterations = 2
minArea = 500
maxArea = 9000
xJitterAmount = 12
yJitterAmount = 9
debugMode = False

# -----------------------------------------------------------------------


bus = smbus.SMBus(1)
vs = PiVideoStream().start() # starting our video stream 
time.sleep(1)
frameComp = None # comparison frame 
averageImage = None # average frame data
mode = 0 # default mode for the turret 
ser = None # serial object
mode = 0 # default mode of 0
threat = 0 # default threat of 0
lastX = 0
lastW = 0
lastY = 0
lastH = 0
written = False

# mode 0 for coordinate sending
# mode 1 to disable turret
# threat 0 laser is off
# threat 1 laser is on
def sendToArduino(mode, threat, x_coord, y_coord):
  global written
  try: # try block to catch i2c errors without aborting code 
    if mode is 0:
        written = False
        data = [threat]
        for n in str(x_coord): # turn numbers into strings 
          data.append(ord(n))
        bus.write_i2c_block_data(address, 0, data) # send each char byte to arduino
        time.sleep(0.1)
        data = [threat]
        for n in str(y_coord):
          data.append(ord(n))
        bus.write_i2c_block_data(address, 1, data)
        time.sleep(0.1)
        data = [threat]
        if debugMode:
          print("[NOTE] Writing x: {0}, y: {1}".format(x_coord, y_coord))
    elif mode is 1:
      if not written:
        bus.write_i2c_block_data(address, 2, [threat])
        written = True
  except IOError:
    print("[NOTE] i2c error")
    pass

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
  except IOError:
    print("[NOTE] Serial error")
    ser = None
    pass

while True:
  # establish serial communication before system starts
  while ser is None:
    arduinoPorts = [p.device for p in lp.comports() if "ACM" in p.description]
    try:
      ser = serial.Serial(arduinoPorts[0], 9600, timeout=0)
      break
    except:
      print("[NOTE] Serial error")
      continue

  # grab a frame from our threaded pivideostream
  f = vs.read()
  # convert the frame to grayscale
  gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) 
  gray = cv2.GaussianBlur(gray, (gassianBlurAmount, gassianBlurAmount), 0)

  # initiate the average
  if averageImage is None: 
    averageImage = numpy.float32(gray)
    continue

  # accumulate the average and convert it to somethin usable 
  cv2.accumulateWeighted(gray, averageImage, accumulateWeight) 
  frameComp = cv2.convertScaleAbs(averageImage)

  # calculate the difference in the frame and return image above threshold
  frameDelta = cv2.absdiff(frameComp, gray)
  threshold = cv2.threshold(frameDelta, acceptableDelta, 255, cv2.THRESH_BINARY)[1]

  # fill in the holes and find the contours
  threshold = cv2.dilate(threshold, None, iterations = dilateIterations)
  (cnts, _) = cv2.findContours(threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) 

  # find the biggest contour within our range
  temp = None
  for c in cnts:
    if cv2.contourArea(c) < minArea or cv2.contourArea(c) > maxArea: 
      continue
    elif temp is None or cv2.contourArea(c) > cv2.contourArea(temp):
      temp = c 

  # check for serial update and ping the arduino
  readSerial()

  # draw boxes around our area of interest, taking into account our jitter reduction
  if temp is not None:
    (x, y, w, h) = cv2.boundingRect(temp)
    if abs(lastX - (x + w/2)) > lastW/xJitterAmount:
      lastX = x + w/2
      lastW = w
    if abs(lastY - (y + h/3)) > lastH/yJitterAmount:
      lastY = y + h/3
      lastH = h
    if debugMode:
      cv2.rectangle(f, (x, y), (x + w, y + h), (0, 255, 0), 1)
    sendToArduino(mode, threat, lastX, lastY)

  # draw things for our debug
  if debugMode:
    cv2.circle(f, (lastX, lastY), 3, (0, 255, 0), 2)
    cv2.imshow("Frames", f)
    cv2.imshow("Thresh", threshold)
    cv2.imshow("frame delta", frameDelta)
    cv2.imshow("avg", frameComp)
    cv2.waitKey(1)