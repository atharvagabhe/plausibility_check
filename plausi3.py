#!usr/bin/python
#encoding:utf-8
'''
1.
configparser
multithreading
traceback


'''
#1.Import
import cv2
import zbar
from PIL import Image
import time
import math
import picamera
import io
import argparse
import threading
import sys
import os
import signal
import numpy as np
from threading import Thread
import RPi.GPIO as GPIO
import spidev
import logging
import ConfigParser 
from picamera.array import PiRGBArray


#2.Declarations
camera=picamera.PiCamera() #camera is camera,not to be changed!
time.sleep(2)
exec(open("/home/pi/plausi_check/settings/camera_settings.txt"))

Config=ConfigParser.ConfigParser()
Config.read("../settings/settings.ini")

spi = spidev.SpiDev()
spi.open(0,0)

logging.basicConfig(filename='../logs/plausicheck.log',filemode='w',level=logging.DEBUG)

PingRate=Config.getfloat("Delay","PingRate")
triggerDistance=Config.getfloat("Sensor","Trigger")
tolerance=Config.getfloat("Sensor","Tolerance")
beltWidth=Config.getfloat("Belt","Width")##
minParcelWidth=Config.getfloat("Sensor","PacketWidth")#According to Holger's Table
contourLow=Config.getint("CV2","ContourLow")
contourHigh=Config.getint("CV2","ContourHigh")
ratio=Config.getint("Belt","Ratio")
xmax=Config.getint("Belt","Xmax")
ymax=Config.getint("Belt","Ymax")
threshold=beltWidth-minParcelWidth


threadflag1=False

threads=[] #threadpool


#4.Threads----------------------------combine all classes for thread handling 
class irThread(Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
    def run(self):
        print "Starting " + self.name
        global detected
        detected=False
        while True:
			try:
				measureDistance()
					
				time.sleep(PingRate)
			except Exception as exc:
				print 'Aborting::'
				logging.info(exc)
        print "Exiting " + self.name


class capdetThread(Thread):
	
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
    def run(self):
		try:	
			global temp
			global threadflag1
			print "Starting " + self.name
			threadflag1=True
			temp=time.time()*1000
			captureDetectSequence()
			capdetThread.exit()
			print "Exiting " + self.name
			threadflag1=False

		except:
			print "Exiting with error" + self.name
			threadflag1=False
#5..Function definitions
def measureDistance():
	global detected
	channel=Config.getint("ADC","Channel")
	val = spi.xfer2([1,(8+channel)<<4,0])
	data = ((val[1]&3) << 8) + val[2]
	v=(data/1023.0)*3.3
  	dist = 16.2537 * v**4 - 129.893 * v**3 + 382.268 * v**2 - 512.611 * v + 301.439
  	print "| Distance | %.2f cm" % dist
  	if dist-tolerance>=threshold:
		detected=False
	elif detected == False and threadflag1==False:
		try:
			detected=True
			threadCD=capdetThread(2,'Capture and Detect Thread')	
			threadCD.start()
			threads.append(threadCD)
			#for t in threads:
			#	t.join()			
		except Exception as exc:
			print exc
			logging.info(exc)
			logging.info('measureDistance')
	else:
		print 'I see a parcel but print nothing'		
def captureImage(var):#take a picture;req1:take to cv obj. req2:format vis a vis image quality size and time required in each step		
	try:
		if var==False:
			image = cv2.imread('/home/pi/plausi_check/160523_recordings/brown.10.jpg')
		else:	
			#stream=PiRGBArray(camera)			
			print "CaptureImage"
			stream = io.BytesIO()
			cvtime=time.time()*1000
			cltime=time.time()*1000
			logging.info('clicktime')
			#logging.info(time.time()*1000-temp)
			
			
			camera.capture(stream,format='jpeg', quality=100, use_video_port=True)
			#camera.capture(stream, format='bgr' ,use_video_port=True)
			#cv2.imshow("asd",stream)
			#image=stream.array
			#print sys.getsizeof(image)					
			data=np.fromstring(stream.getvalue(),dtype=np.uint8)
			image=cv2.imdecode(data,1)			
			print sys.getsizeof(stream)
			cvtime=time.time()*1000-cvtime				
			logging.info(cvtime)			
			cv2.imwrite("/home/pi/plausi_check/TestImages/img_" + str(cvtime)+".jpg",image)
			#stream.seek(0)
			#stream.truncate()			
			print 'cvtime:',cvtime
		return image
	except Exception as exc:
		print exc
		logging.info(exc)
	
def cropImage(img):#function to seperate mirror and belt
	#mirror=img.copy()
	#img = cv2.resize(img,(1024,768))
	#ratio = 2.53125
	mirror = img[Config.getfloat("Mirror","YLow"):Config.getfloat("Mirror","YHigh"),Config.getfloat("Mirror","XLow"):Config.getfloat("Mirror","XHigh")]
	mirror= cv2.resize(mirror,(100,400))
	mirror=rotateImage(mirror,-3)
	#label=img.copy()
	label = img[Config.getfloat("Belt","YLow"):Config.getfloat("Belt","YHigh"),Config.getfloat("Belt","XLow"):Config.getfloat("Belt","XHigh")]
	return mirror,label
	
	
	
def findLabel(img2):#should take an argument,output of captureImage()
	try:
		
		newPoints=None
		#img2  = img.copy()
		img = cv2.resize(img2,(xmax/ratio,ymax/ratio))###
		#ratio = 2###
		#print ratio
		gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
		ret,gray = cv2.threshold(gray,Config.getint("CV2","Threshold"),255,0) #old was 175 ###th--var
		#gray2 = gray.copy()
		_,contours,_= cv2.findContours(gray,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
		
		for cnt in contours:
			if contourLow<cv2.contourArea(cnt)<contourHigh:# thirty-thousand to hundred-thousand
				rect = cv2.minAreaRect(cnt) 
				points = cv2.boxPoints(rect)
    
				newPoints = ratio*np.array(points)		
				newPoints = np.int0(newPoints)
				#uncomment to see result
				#cv2.drawContours(img2, [newPoints], -1, (0, 255, 0), 3)	
		#cv2.imshow('contours',img2) 
		ymin= newPoints[np.argmin(newPoints[:,1]),1]
		ymax= newPoints[np.argmax(newPoints[:,1]),1]
		xmin= newPoints[np.argmin(newPoints[:,0]),0]
		xmax= newPoints[np.argmax(newPoints[:,0]),0]
		#print "Checkpoint 3"
		cropped_label=img2[ymin:ymax,xmin:xmax]
		angle = degreeImage(newPoints)
		#print angle
		if angle>=45:
			rotated_image = rotateImage(cropped_label,(angle-90))
		else:
			rotated_image = rotateImage(cropped_label,angle)

		return rotated_image #what if it fails??
	except Exception as exc:
		print exc
		logging.info(exc)
		logging.info('findLabel')
		
def rotateImage(image,degree):
	try:
		rows,cols,_=image.shape
		M=cv2.getRotationMatrix2D((cols/2,rows/2),degree,1)
		dst=cv2.warpAffine(image,M,(cols,rows))
		return dst
	except Exception as exc:
		print exc
		logging.info(exc)
def degreeImage(newPoints):
	ymin= newPoints[np.argmin(newPoints[:,1]),1]
	xymax = newPoints[np.argmax(newPoints[:,1]),0]

	ymax= newPoints[np.argmax(newPoints[:,1]),1]
	xmin= newPoints[np.argmin(newPoints[:,0]),0]
	yxmin= newPoints[np.argmin(newPoints[:,0]),1]	
	xmax= newPoints[np.argmax(newPoints[:,0]),0]
	a = abs(xmin - xymax)
	c = math.hypot(a, yxmin-ymax)
	#division by ZERO!!	
	if c == 0:
		return 0	
	angle = math.acos(float (a)/float(c))	
	print angle
	return math.degrees(angle)

def scan(image):
	global threadflag1
	try:
		
		# create a Processor
		# create a reader
		scanner = zbar.ImageScanner()
	
		# configure the reader
		scanner.parse_config('enable')

		# obtain image data
		#pil = Image.open(image).convert('L')
		pil = Image.fromarray(image).convert('L')
		width, height = pil.size

		beginTime = time.time()*1000
		raw = pil.tobytes()

		# wrap image data
		image = zbar.Image(width, height, 'Y800', raw)

		# scan the image for barcodes
		scanner.scan(image)
		
		# extract results
		for symbol in image:
			print 'decoded', symbol.type, 'symbol', ' "%s" ' % symbol.data
			
		
		# clean up
		del(image)
		
	except Exception as exc:
		
		print exc
		logging.info(exc)
	threadflag1=False
	
def captureDetectSequence():
	global threadflag1
	try:
		startTime=time.time()*1000	
		capturedImage=captureImage(True)				
		mirrorImage,labelImage=cropImage(capturedImage)
		labelImage=findLabel(labelImage)
		if labelImage!=None:
			scan(mirrorImage)
			scan(labelImage)
		else:
			print 'No label found exiting.'
			#this shud call the scan function with the whole image
			
	except Exception as exc:
		
		logging.info(exc)
	threadflag1=False		
	
#6.Main	
#pseudo
if __name__=='__main__':	
	try:
		threadIR=irThread(1,'Distance Sensor Thread')	
		threadIR.start()
		threads.append(threadIR)
		#for t in threads:
		#	t.join()
		#print t			
	except Exception as exc:	
			print exc
			logging.info(exc)
	time.sleep(PingRate)

