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
import scd30

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
pumpSched = 5
pumpTime = 10
door = 25
drawer = 22
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
fan1State = True
fan2State = True
fan3State = True
off = 1
on = 0
global flow_cnt
flow_cnt = 0

PIGPIO_HOST = '::1'
I2C_SLAVE = 0x61
I2C_BUS = 1

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
	motorState = True
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
	global flow_cnt
	flow_cnt = 0
	if GPIO.input(door)==opened:
		GPIO.output(pump, off)
	elif GPIO.input(door)==closed:	
		GPIO.output(pump, on)
		time.sleep(pumpTime)
		print("Pump running")
		GPIO.output(pump, off) 
		print("Pump off")
		LPM = round(((((flow_cnt/pumpTime)*7.5) + 22.5)/60),2)

def LED():
	ledState = True
	dim1Duty = 40
	if ledState == 0 and GPIO.input(door)== opened:
		DIM1.ChangeDutyCycle(doorDim)
	else:
		DIM1.ChangeDutyCycle(dim1Duty)	
	GPIO.output(led, ledState)

def Fan1():
	fan1State = True
	GPIO.output(fan1, fan1State)
	return fan1State
	
def Fan2():
	fan2State = True
	GPIO.output(fan2, fan2State)
	return fan2State
	
def Fan3():
	fan3State = True
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
	sensor = scd30.SCD30(PIGPIO_HOST, I2C_SLAVE, I2C_BUS)

	# trigger continous measurement
	sensor.sendCommand(scd30.COMMAND_CONTINUOUS_MEASUREMENT, 970)

	# enable autocalibration
	sensor.sendCommand(scd30.COMMAND_AUTOMATIC_SELF_CALIBRATION, 1)

	sensor.waitForDataReady()
	try:
		# read measurement
		data = sensor.readMeasurement()

		if (data == False):
			exit(1)

		[float_co2, float_T, float_rH] = data

		if float_co2 > 0.0:
			print("gas_ppm{sensor=\"SCD30\",gas=\"CO2\"} %f" % float_co2)

		print("temperature_degC{sensor=\"SCD30\"} %f" % float_T)

		if float_rH > 0.0:
			print("humidity_rel_percent{sensor=\"SCD30\"} %f" % float_rH)
	except OSError:
		sensor.close()
		pass

def Flow(FLOW_SENSOR):
	global flow_cnt
	flow_cnt += 1
	
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
	GPIO.output(pump, true)
	
def Camera():
	try:
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
		except OSError:
			pass
			
GPIO.setup(led, GPIO.OUT)
GPIO.setup(fan1, GPIO.OUT)
GPIO.setup(fan2, GPIO.OUT)
GPIO.setup(fan3, GPIO.OUT)
GPIO.setup(pump, GPIO.OUT)

GPIO.add_event_detect(door, GPIO.RISING)
GPIO.add_event_callback(door, doorOpen)
GPIO.add_event_detect(FLOW_SENSOR, GPIO.BOTH, callback=Pulse_count, bouncetime=12)
GPIO.output(pump, off)
schedule.every(pumpSched).minutes.do(Pump)

while True:
	#use functions below to add automation to your garden
	LED() 
	Fan1()
	Fan2()
	Fan3()
	PH()
	EC()
	Temp_humid()
	Level()
	Motor()
	schedule.run_pending()
	time.sleep(0.4)

	
		
# Reset all gpio pin
#GPIO.cleanup()
  
