# imports 
from imutils.video.pivideostream import PiVideoStream # juicy threading support
import numpy
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
serial = None # serial object
state = 0 # default state of 0
threat = 0 # default threat of 0

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
    bus.write_byte_data(address, 2)

def readSerial():
  # check serial, default state gets returned if no update or no serial connection
  if serial is None:
    try:
      serial = serial.Serial('/dev/ttyACM0', 9600)
    except:
      print("[NOTE] Unable to open serial connection.")
      return (state, threat)
  serial.readline()
  #XXX do something with the read line 
  return (state, threat)
  

while True:
  f = vs.read() # grab a frame from our threaded pivideostream
  gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) # convert the frame to grayscale
  gray = cv2.GaussianBlur(gray, (11, 11), 0) # computationally expensive gassian blur

  if averageImage is None: # start the average
    averageImage = numpy.float32(gray)
    continue

  cv2.accumulateWeighted(gray, averageImage, 0.4) # accumulate the average frame
  frameComp = cv2.convertScaleAbs(averageImage) # take the average image and convert it to our comparison img

  frameDelta = cv2.absdiff(frameComp, gray) # calculate the delta frame between our avg and current frame
  threshold = cv2.threshold(frameDelta, 5, 255, cv2.THRESH_BINARY)[1] # return data above threshold

  threshold = cv2.dilate(threshold, None, iterations = 4) # dilate our threshold to fill out holes
  (cnts, _) = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # build our delta areas

  temp = None
  for c in cnts:
    if cv2.contourArea(c) < 1500 or cv2.contourArea(c) > 20000: 
      continue # if contour is bigger than our bounds, ignore
    elif temp is None or cv2.contourArea(c) > cv2.contourArea(temp):
      temp = c # grab the biggest contour that's within our bounds 

  if temp is not None: # draw boxes around our area of interest
    (x, y, w, h) = cv2.boundingRect(temp)
    cv2.rectangle(f, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.putText(f, str(cv2.boundingRect(temp)), (10, 20), cv2.FONT_HERSHEY_PLAIN, 1,  (0, 255, 0), 1)
    (st, thr) = readSerial()
    sendToArduino(st, thr, (x + w/2), (y + h/2)) #XXX: finish threat logic

  # XXX: increase computational capacity by deleting the draw later
  cv2.imshow("Frames", f)
  key = cv2.waitKey(1) & 0xFF