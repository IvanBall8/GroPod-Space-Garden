#!/usr/bin/python
#---------------------------- Import Stuff ---------------------------
import RPi.GPIO as GPIO
import time
import datetime
import threading
import os
import schedule
import json
import random
import smbus
import picamera

#------------------------- Create Variables -------------------------
growPodId = "NASAChallenge" #01GB345H
led = 17
fan1 = 7
fan2 = 6
fan3 = 16
valve = 23
relay = 20
pump = 4
flow = 111
pumpState = 1
pumpSched = 5
pumpTime = 60
door = 25
opened = True
closed = False
doorDim = 0
motorDir = 23
motorStep = 24
motorEN = 21
SPR = 200
step_count = SPR * 8 #step_count = SPR * step resolution
motorDelay = .0208 / 16 
CW = 1     # Clockwise Rotation
CCW = 0    # Counterclockwise Rotation
step = 1
Turn = 0
LVL_T = 14
LVL_E = 7
FLOW_SENSOR = 12
PWM0 = 18
PWM1 = 13
PROX1 = 5
#------------------------- Initialize GPIO -------------------------
# Set GPIO mode: GPIO.BCM or GPIO.BOARD
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Set mode for each gpio pin
GPIO.setup(led, GPIO.OUT)
GPIO.setup(fan1, GPIO.OUT)
GPIO.setup(fan2, GPIO.OUT)
GPIO.setup(fan3, GPIO.OUT)
GPIO.setup(pump, GPIO.OUT)
GPIO.setup(door, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(drawer, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(sysPower, GPIO.OUT)
GPIO.setup(motorDir, GPIO.OUT)
GPIO.setup(motorStep, GPIO.OUT) 
GPIO.setup(motorEN, GPIO.OUT)
GPIO.setup(FLOW_SENSOR, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LVL_T, GPIO.OUT)
GPIO.setup(LVL_E, GPIO.IN)
GPIO.setup(PWM0, GPIO.OUT)   
GPIO.setup(PWM1, GPIO.OUT) 
GPIO.setup(PROX1, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#Set GPIO state
GPIO.output(motorEN, GPIO.HIGH)
GPIO.output(LVL_T, GPIO.LOW)
GPIO.output(motorDir, 1)
GPIO.add_event_detect(FLOW_SENSOR, GPIO.RISING)
DIM1 = GPIO.PWM(PWM0, 1000)    # create PWM at 1KHz
DIM2 = GPIO.PWM(PWM1, 1000)    # create PWM at 1KHz
DIM1.start(0)                # start the PWM with a 0 percent duty cycle (off)
DIM2.start(0)                # start the PWM with a 0 percent duty cycle (off)

# Get I2C bus
bus = smbus.SMBus(1)

#--------------------------- Controls ----------------------------
def Motor():
	motorState = 1
	GPIO.output(motorEN, GPIO.LOW)
	if GPIO.input(door)==closed and motorState ==1:
		GPIO.output(motorDir, CW) #initialize direction of stepper
		mtr = 1
		for x in range(step_count):
			GPIO.output(motorStep, GPIO.HIGH)
			time.sleep(motorDelay)
			print("Motor step",x)
			GPIO.output(motorStep, GPIO.LOW)
			time.sleep(motorDelay)
	else:
		mtr = 0
	GPIO.output(motorEN, GPIO.HIGH)
	
def Pump():
	pumpState = 1
	if GPIO.input(door)==opened or GPIO.input(drawer)==opened:
		GPIO.output(pump, off)
	elif GPIO.input(door)==closed and GPIO.input(drawer)==closed and pumpState == on:	
		GPIO.output(pump, pumpState)
		time.sleep(pumpTime)
		print("Pump running")
		GPIO.output(pump, off) 
		print("Pump off")

def LED():
	ledState = 1
	if ledState == 0 and GPIO.input(door)== opened:
		DIM1.ChangeDutyCycle(doorDim)
	else:
		DIM1.ChangeDutyCycle(dim1Duty)
		
	GPIO.output(led1, ledState)

def Fan1():
	fan1State = 1
	GPIO.output(fan1, fan1State)
	return fan1State
	
def Fan2():
	fan2State = 1
	GPIO.output(fan2, fan2State)
	return fan2State
	
def Fan3():
	fan3State = 1
	GPIO.output(fan3, fan3State)
	return fan3State
	
#--------------------------- Sensors -------------------------------

def PH():
	val = (((3.5 * mcp.read_adc(1))/310.3) + 2)
	return round(val, 2)

def EC():
	val = ((3.5 * (mcp.read_adc(0))) - 244)
	return round(val, 2)

def Temp_humid():
	# SI7021 address, 0x40(64)
	# 0xF5(245)	Select Relative Humidity NO HOLD master mode
	try:
		bus.write_byte(0x40, 0xF5)
		time.sleep(0.1)
		# SI7021 address, 0x40(64)
		# Read data back, 2 bytes, Humidity MSB first
		data0 = bus.read_byte(0x40)
		data1 = bus.read_byte(0x40)
		# Convert the data
		humidity = round(((data0 * 256 + data1) * 125 / 65536.0) - 6, 2)
		time.sleep(0.1)
		# SI7021 address, 0x40(64)
		# 0xF3(243)	Select temperature NO HOLD master mode
		bus.write_byte(0x40, 0xF3)
		time.sleep(0.1)
		# SI7021 address, 0x40(64)
		# Read data back, 2 bytes, Temperature MSB first
		data0 = bus.read_byte(0x40)
		data1 = bus.read_byte(0x40)
		# Convert the data
		cTemp = ((data0 * 256 + data1) * 175.72 / 65536.0) - 46.85
		fTemp = round(cTemp * 1.8 + 32, 2)	
	except OSError:
		pass

def Level():
	try:
		GPIO.output(LVL_T, False)
		time.sleep(2)
		# This function measures a distance
		GPIO.output(LVL_T, True)
		time.sleep(0.00001)
		GPIO.output(LVL_T, False)
		sonar_signal_off = time.time()
		echo_status_counter = 1	
		while GPIO.input(LVL_E) == 0:
			if echo_status_counter < 1000:
				sonar_signal_off = time.time()
				echo_status_counter += 1
			else:
				print("Echo pulse was not received")
				echo_status_counter = 0
				break		
		while GPIO.input(LVL_E) == 1:
			sonar_signal_on = time.time()	
		if echo_status_counter != 0:
			elapsed = sonar_signal_on - sonar_signal_off
			distance = (elapsed * 34496)/2
			print("DIST: %f" % distance)
			return round(distance,2)
		else:
			return 0		
	except UnboundLocalError:
		return 0
		pass
	GPIO.cleanup((LVL_T, LVL_E))

def doorOpen(door):
	DIM1.ChangeDutyCycle(doorDim)
	DIM2.ChangeDutyCycle(doorDim)
	GPIO.output(pump, off)

def drawerOpen(drawer):
	GPIO.output(pump, off)


GPIO.add_event_callback(door, doorOpen)
GPIO.add_event_detect(drawer, GPIO.RISING)
GPIO.add_event_callback(drawer, drawerOpen)

schedule.every(pumpSched).minutes.do(Pump)

while True:
	fan_1 = Fan1()
	fan_2 = Fan2()
	fan_3 = Fan3()
	led_1,dim1 = LED1()
	led_2,dim2 = LED2()
	motor = Motor()
	schedule.run_pending()
	time.sleep(0.4)
	hour = datetime.datetime.now().hour
	if (hour > 6 and hour <= 21):
		timeGood = 1
	elif hour>21 and hour<=5:
		timeGood = 0
	
	Reed1 = GPIO.input(PROX1)
	if Reed1 == closed and state == open and timeGood == 1:
		GPIO.output(LED, 1)
		print("switch closed")
		state = closed
		print "Time" , datetime.datetime.now()
		print "timeGood =", timeGood
		time.sleep(1)
		date = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
		os.system("fswebcam -r 2592x1944 -S 3 --jpeg 50 --delay 3 --set brightness=10% --save /media/exfat/TimeLapse6/"+ date +".jpg")

	elif Reed1 == open and state == closed:
		print("switch open")
		state = open

# Reset all gpio pin
GPIO.cleanup()
  
