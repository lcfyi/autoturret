# imports 
from imutils.video.pivideostream import PiVideoStream # juicy threading support
import numpy
import math
import time
import cv2
import serial
import serial.tools.list_ports as lp
import pigpio

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

tilt = 6
pan = 5

piPin = pigpio.pi()


# designed specifically for parallax standard servos
def servoControl(servo, angle):
  #map 515 to 2250
  eachAngle = (2450-515)/180
  piPin.set_servo_pulsewidth(servo, int(515 + angle*eachAngle))

def coordMap(num, oldLow, oldHigh, newLow, newHigh):
  oldRange = oldHigh - oldLow
  newRange = newHigh - newLow
  return (newLow + num * newRange/oldRange)

# mode 0 for coordinate sending
# mode 1 to disable turret
# threat 0 laser is off
# threat 1 laser is on
def adjustAngle(mode, threat, x_coord, y_coord):
  if mode is 0:
    servoControl(pan, coordMap(x_coord, 1, 320, 105, 25))
    servoControl(tilt, coordMap(y_coord, 1, 240, 55, 110))
    print("[NOTE] Writing x: " + str(x_coord) + ", y: " + str(y_coord))
  elif mode is 1:
    return


def readSerial():
  try:
    # global variables
    global mode
    global threat
    global ser
    ser.write(str(1))
    if ser.in_waiting:
      mode_and_threat = int(ser.readline())
      threat = mode_and_threat % 10
      mode = int(math.floor(mode_and_threat / 10)) % 10
      print("[NOTE] Mode updated to " + str(mode))
      print("[NOTE] Threat updated to " + str(threat))
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

  f = vs.read() # grab a frame from our threaded pivideostream
  gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) # convert the frame to grayscale
  gray = cv2.GaussianBlur(gray, (11, 11), 0) # computationally expensive gassian blur

  if averageImage is None: # start the average
    averageImage = numpy.float32(gray)
    continue

  cv2.accumulateWeighted(gray, averageImage, 0.4) # accumulate the average frame
  frameComp = cv2.convertScaleAbs(averageImage) # take the average image and convert it to our comparison img

  frameDelta = cv2.absdiff(frameComp, gray) # calculate the delta frame between our avg and current frame
  threshold = cv2.threshold(frameDelta, 6, 255, cv2.THRESH_BINARY)[1] # return data above threshold

  threshold = cv2.dilate(threshold, None, iterations = 2) # dilate our threshold to fill out holes
  (cnts, _) = cv2.findContours(threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # build our delta areas

  temp = None
  for c in cnts:
    if cv2.contourArea(c) < 500 or cv2.contourArea(c) > 9000: 
      continue # if contour is bigger than our bounds, ignore
    elif temp is None or cv2.contourArea(c) > cv2.contourArea(temp):
      temp = c # grab the biggest contour that's within our bounds 

  # update mode and threat state
  readSerial()

  if temp is not None: # draw boxes around our area of interest
    (x, y, w, h) = cv2.boundingRect(temp)
    if abs(lastX - (x + w/2)) > lastW/8:
      lastX = x + w/2
      lastW = w
    if abs(lastY - (y + h/2)) > lastH/6:
      lastY = y + h/3
      lastH = h
    #cv2.circle(f, (lastX, lastY), 3, (0, 255, 0), 2)
    cv2.rectangle(f, (x, y), (x + w, y + h), (0, 255, 0), 1)
    adjustAngle(mode, threat, lastX, lastY) #XXX: finish threat logic
  cv2.circle(f, (lastX, lastY), 3, (0, 255, 0), 2)

  # XXX: increase computational capacity by deleting the draw later
  cv2.imshow("Frames", f)
  cv2.imshow("Thresh", threshold)
  cv2.imshow("frame delta", frameDelta)
  cv2.imshow("avg", frameComp)

  key = cv2.waitKey(1) & 0xFF