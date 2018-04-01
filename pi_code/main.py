# imports 
from imutils.video.pivideostream import PiVideoStream # juicy threading support
import numpy
import math
import time
import cv2
import smbus
import serial

# global variables and objects
bus = smbus.SMBus(1) # smbus 1 on the pi is userfacing
address = 0x08 # address of the Arduino

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

# mode 0 for coordinate sending
# mode 1 to disable turret
# threat 0 laser is off
# threat 1 laser is on
def sendToArduino(mode, threat = 0, x_coord = None, y_coord = None):
  if mode is 0:
    try: # try block to catch i2c errors without aborting code 
      data = [threat]
      time.sleep(0.05)
      for n in str(x_coord): # turn numbers into strings 
        data.append(ord(n))
      bus.write_i2c_block_data(address, 0, data) # send each char byte to arduino
      data = [threat]
      for n in str(y_coord):
        data.append(ord(n))
      bus.write_i2c_block_data(address, 1, data)
      data = [threat]
      print("[NOTE] Writing x: " + str(x_coord) + ", y: " + str(y_coord))
    except IOError:
      print("[NOTE] i2c error")
      pass
  elif mode is 1:
    bus.write_i2c_block_data(address, 2, [threat])

def readSerial():
  # global variables
  global mode
  global threat
  global ser
  # check serial, default state gets returned if no update or no serial connection
  if ser is None:
    return
  while ser.in_waiting:
    mode_and_threat = int(ser.readline())
    mode = mode_and_threat % 10
    threat = int(math.floor(mode_and_threat / 10)) % 10

while True:
  f = vs.read() # grab a frame from our threaded pivideostream
  gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) # convert the frame to grayscale
  gray = cv2.GaussianBlur(gray, (13, 13), 0) # computationally expensive gassian blur
  
  if averageImage is None: # start the average
    averageImage = numpy.float32(gray)
    continue

  cv2.accumulateWeighted(gray, averageImage, 0.3) # accumulate the average frame
  frameComp = cv2.convertScaleAbs(averageImage) # take the average image and convert it to our comparison img

  frameDelta = cv2.absdiff(frameComp, gray) # calculate the delta frame between our avg and current frame
  threshold = cv2.threshold(frameDelta, 10, 255, cv2.THRESH_BINARY)[1] # return data above threshold

  threshold = cv2.dilate(threshold, None, iterations = 3) # dilate our threshold to fill out holes
  (cnts, _) = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # build our delta areas

  temp = None
  for c in cnts:
    if cv2.contourArea(c) < 500 or cv2.contourArea(c) > 7000: 
      continue # if contour is bigger than our bounds, ignore
    elif temp is None or cv2.contourArea(c) > cv2.contourArea(temp):
      temp = c # grab the biggest contour that's within our bounds 

  # update mode and threat state
  if ser is None:
    try:
      ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    except:
      print("[NOTE] Unable to open serial connection.")
  readSerial()

  if temp is not None: # draw boxes around our area of interest
    (x, y, w, h) = cv2.boundingRect(temp)
    if abs(lastX - (x + w/2)) > lastW/8:
      lastX = x + w/2
      lastW = w
    if abs(lastY - (y + h/2)) > lastH/6:
      lastY = y + h/2
      lastH = h
    #cv2.circle(f, (lastX, lastY), 3, (0, 255, 0), 2)
    cv2.rectangle(f, (x, y), (x + w, y + h), (0, 255, 0), 1)
    sendToArduino(mode, threat, lastX, lastY) #XXX: finish threat logic
  cv2.circle(f, (lastX, lastY), 3, (0, 255, 0), 2)

  # XXX: increase computational capacity by deleting the draw later
  cv2.imshow("Frames", f)
  cv2.imshow("Thresh", threshold)
  cv2.imshow("frame delta", frameDelta)
  cv2.imshow("avg", frameComp)

  key = cv2.waitKey(1) & 0xFF