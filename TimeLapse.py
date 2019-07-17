#!/usr/bin/python

import time
import datetime
from picamera import PiCamera
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
PROX1 = 5
LED = 17

GPIO.setwarnings(False)

GPIO.setup(PROX1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
open = 1
closed = 0
state = open
GPIO.setup(LED, GPIO.OUT, initial=GPIO.LOW)

time.sleep(1)

camera = PiCamera()

while True:
	hour = datetime.datetime.now().hour
	print "hour =", hour
	if (hour > 6 and hour <= 21):
		timeGood = 1
	elif hour>21 and hour<=5:
		timeGood = 0
	print "timeGood =", timeGood
	
	Reed1 = GPIO.input(PROX1)
	if Reed1 == closed and state == open and timeGood == 1:
		GPIO.output(LED, 1)
		print("switch closed")
		state = closed
		time.sleep(1)
		print "1"
		camera.resolution = (2592, 1944)
		print "2"
		camera.vflip = True
		print "3"
		date = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
		print "4"
		camera.start_preview()
		print "5"
		time.sleep(2)
		print "6"
		camera.capture("/media/exfat/TimeLapse6/"+ date +".jpg")
		print "7"
		print("Picture Taken")
		camera.stop_preview()
		time.sleep(20)
		GPIO.output(LED, 0)
	elif Reed1 == open and state == closed:
		print("switch open")
		state = open
	
	time.sleep(5)
  
