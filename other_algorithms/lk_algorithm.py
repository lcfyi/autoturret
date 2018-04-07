import datetime
import math
import numpy as np
import imutils
import time
import cv2
import serial
import serial.tools.list_ports as lp
from time import clock 
import argparse

camera = cv2.VideoCapture(0)
time.sleep(0.5)
parser = argparse.ArgumentParser()
parser.add_argument("--debug", help="this will print out status messages", action="store_true")
args = parser.parse_args()
debugMode = args.debug

class absDiffTrack:
  def __init__(self):
    self._ = None
    self.last_coords = [0, 0, 0, 0]

  def scan(self, frame, average):
    gray = cv2.GaussianBlur(frame, (21,21), 0)
    frameComp = cv2.convertScaleAbs(average)
    frameDelta = cv2.absdiff(gray, frameComp)
    thresh = cv2.threshold(frameDelta, 3, 255, cv2.THRESH_BINARY)[1]

    thresh = cv2.dilate(thresh, None, iterations = 3)
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_TREE,
      cv2.CHAIN_APPROX_SIMPLE)[1]
    temp = None

    for c in cnts:
      if cv2.contourArea(c) < 5000 or cv2.contourArea(c) > 30000:
        continue
      if temp is None or cv2.contourArea(c) > cv2.contourArea(temp):
        temp = c

    if temp is not None:
      (x, y, w, h) = cv2.boundingRect(temp)
      if (abs(self.last_coords[0] - x) < 10) and (abs(self.last_coords[1] - y) < 10):
        return (x + w/2, y + h/2)
      else:
        self.last_coords = cv2.boundingRect(temp)
    return

lk_params = dict( winSize  = (10, 10),
                  maxLevel = 3,
                  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))


abs_diff = absDiffTrack()
lost = True
p0 = None
color = np.random.randint(0, 255, (100,3))
prev_gray = None
avg_image = None

while True:
  (grabbed, frame) = camera.read()
  frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
  if debugMode:
    print("In loop")
  if avg_image is None:
    avg_image = np.float32(frame_gray)
    continue
  
  cv2.accumulateWeighted(frame_gray, avg_image, 0.5)

  if prev_gray is None:
    prev_gray = frame_gray
    continue

  if lost:
    new_coords = abs_diff.scan(frame_gray, avg_image)
    if new_coords is not None:
      lost = False
      p0 = np.float32([new_coords]).reshape(-1, 1, 2)
  else:
    p1, st, err = cv2.calcOpticalFlowPyrLK(prev_gray, frame_gray, p0, None, **lk_params)

    abs_diff.scan(frame_gray, avg_image)
    try:
      good_new = p1[st==1]
      good_old = p0[st==1]

    except TypeError:
      lost = True
      continue

    if (abs((good_new) - (good_old)) < 0.005).any():
      lost = True
      continue

    for i,(new,old) in enumerate(zip(good_new, good_old)):
      a,b = new.ravel()
      cv2.circle(frame, (a, b), 5, (0, 0, 255), 10)
    p0 = good_new.reshape(-1, 1, 2)
  
  prev_gray = frame_gray
    

  cv2.imshow('frame', frame)
  cv2.waitKey(1)