#Sensor pkgs
import serial
import time
import subprocess32
from subprocess32 import Popen, PIPE, STDOUT

#PID pkgs
import PID
import time
import os.path

#communicating with AWS
import requests

#start serial RPi<-Arduino
ser = serial.Serial('/dev/ttyACM0',9600)
line = 0
sensorInfo = " "
temp = 0
hum = 0

#initialize actuator subprocesses
heat_process = Popen(['python', 'heatingElement.py', '0'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
hum_process = Popen(['python', 'humidityElement.py', '0'], stdout=PIPE, stdin=PIPE, stderr=PIPE)

#set PID targets
targetT = 70  #target temperature
P_temp = 20
I_temp = 0
D_temp = 1

targetH = 50  #target humidity
P_hum = 1
I_hum = 0
D_hum = 35

#create PID controllers
pid_temp = PID.PID(P_temp, I_temp, D_temp)
pid_temp.SetPoint = targetT
pid_temp.setSampleTime(1)

pid_hum = PID.PID(P_hum, I_hum, D_hum)
pid_hum.SetPoint = targetH
pid_hum.setSampleTime(1)

#define operating functions
def listen():

    global line,ser,sensorInfo,temp,hum #load in global vars

    if(ser.in_waiting > 0): #listen for data
        sensorInfo = str.strip(ser.readline()).split(' ')
    if len(sensorInfo)<2:
        pass
    else:
        #print(sensorInfo) #print and save our data
        hum =float(sensorInfo[0])
        temp =float(sensorInfo[1])

        ser.reset_input_buffer()

#start clock
start = time.time()

#start the loop
try:
	while 1:
		#initialize program
		listen()

		#feed the data into our PID
		pid_temp.update(temp)
		pid_hum.update(hum)

		#PID response
		#temp:
		tempPID_out = pid_temp.output
		tempPID_out = max( min( int(tempPID_out), 100 ),0)
		print "Target Temperature: %.1f F | Current: %.1f F | Temp_PID: %s %%"%(targetT, temp, tempPID_out)

		#hum
		humPID_out = pid_hum.output
        	humPID_out = max( min( int(humPID_out), 100 ),0)
        	print "Target Humidity: %.1f %% | Current: %.1f %% | Hum_PID: %s %%"%(targetH, hum, humPID_out)

		if time.time() - start > 5:
			try:
				start = time.time()
				#print('yo1')
				requests.post('http://184.72.68.192:3000/api/heartbeat', json={'temp':temp, 'hum':hum}, timeout=10)
				#print('yo2')
				params = requests.get('http://184.72.68.192:3000/api/params', timeout=10).json()
				#print('yo3')
				#print(params)
				targetT = params['tempDes']
				targetH = params['humDes']
				#print('yo4')
				pid_temp.SetPoint = targetT
				pid_hum.SetPoint = targetH
				#print('yo5')
			except:
				pass


		#poll subprocesses and relaunch if necessary
		poll_heat = heat_process.poll()
		if poll_heat is not None:
			heat_process = Popen(['python', 'heatingElement.py', str(tempPID_out)], stdout=PIPE, stdin=PIPE, stderr=PIPE)
		poll_hum = hum_process.poll()
                if poll_hum is not None:
			hum_process = Popen(['python', 'humidityElement.py', str(humPID_out)], stdout=PIPE, stdin=PIPE, stderr=PIPE)

		#line marks one interation of main loop
		print '----------------------------------------'
		time.sleep(0.5)

except KeyboardInterrupt:
	heat_process.terminate()
	heat_process.wait()
	hum_process.terminate()
	hum_process.wait()