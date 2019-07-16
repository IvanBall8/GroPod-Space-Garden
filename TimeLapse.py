import time
import datetime
import picamera
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
PROX1 = 2

GPIO.setup(PROX1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
open = 1
closed = 0
state = open

while True:
	Reed1 =  GPRIO.input(PROX1)
	if Reed1 ==closed and state == open:
		print("switch closed")
		state = closed
		time.sleep(1)
		with picamera.PiCamera() as camera:
		camera.resolution = (2592, 1944)
		camera.vflip = True
		date = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
		camera.start_preview()
		time.sleep(5)
		camera.capture("/home/pi/TimeLapse5/"+ date +".jpg")
		print("Picture Taken")
		time.sleep(350)
	elif Reed1 == open and state == closed:
		print("switch open")
		state = open
	time.sleep(2)
  
