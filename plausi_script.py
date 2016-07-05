#!usr/bin/python
#encoding:utf-8
'''
1.
argumentparser
configparser
multithreading



'''
#1.Import
import cv2
import sys
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
from picamera.array import PiRGBArray


#2.Declarations

spi = spidev.SpiDev()
spi.open(0,0)
logging.basicConfig(filename='../logs/plausicheck.log',filemode='w',level=logging.DEBUG)
distSensorPingRate=0.1
triggerDistance=40
tolerance=5
beltWidth=80##
minParcelWidth=23#According to Holger's Table
#3.Configuration

#4.Classes
class scanThread (Thread):
    def __init__(self, threadID, name, image):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.image = image
    def run(self):
        print "Starting " + self.name
        scan(self.name,self.image)
        print "Exiting " + self.name


#5..Function definitions
def measureDistance(channel):
	val = spi.xfer2([1,(8+channel)<<4,0])
	data = ((val[1]&3) << 8) + val[2]
	v=(data/1023.0)*3.3
  	dist = 16.2537 * v**4 - 129.893 * v**3 + 382.268 * v**2 - 512.611 * v + 301.439
  	print "Distance: %.2f cm" % dist
	
	
	return dist
	
def captureImage(var=True):#take a picture;req1:take to cv obj. req2:format vis a vis image quality size and time required in each step	
	try:
		if var==False:
			image = cv2.imread('/home/pi/plausi_check/160523_recordings/brown.10.jpg')
		else:
			print 'Capturing Image'
			cvtime=time.time()*1000
			camera.capture(stream, 'bgr',use_video_port=True)									
			image=stream.array			
			#cv2.imwrite("img_" + str(cvtime)+".jpg",image)
			#data=np.fromstring(stream.getvalue(),dtype=np.uint8)
			#image=cv2.imdecode(data,1)
			cvtime=time.time()*1000-cvtime			
			print 'cvtime:',cvtime
			stream.truncate(0)			
		return image
	except Exception as exc:
		print exc#
		logging.info(exc)
	
def cropImage(img):#function to seperate mirror and belt
	#mirror=img.copy()
	#img = cv2.resize(img,(1024,768))
	#ratio = 2.53125
	mirror = img[350:1550,200:500]
	mirror= cv2.resize(mirror,(100,400))
	mirror=rotateImage(mirror,-3)
	#label=img.copy()
	label = img[0:1550,500:2200]
	return mirror,label
	
	
	
def findLabel(img2):#should take an argument,output of captureImage()
	try:
		
		#img2  = img.copy()
		img = cv2.resize(img2,(1700/2,1550/2))###
		ratio = 2###
		print ratio
		gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
		ret,gray = cv2.threshold(gray,200,255,0) #old was 175 ###th--var
		#gray2 = gray.copy()
		_,contours,_= cv2.findContours(gray,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
		print "Checkpoint 1"
		for cnt in contours:
			if 30000<cv2.contourArea(cnt)<100000:# thirty-thousand to hundred-thousand
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
		
def rotateImage(image,degree):
	rows,cols,_=image.shape
	M=cv2.getRotationMatrix2D((cols/2,rows/2),degree,1)
	dst=cv2.warpAffine(image,M,(cols,rows))
	return dst

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

def scan(threadname,image):
	try:
		print 'am in scan'
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
	
#6.Main	
#pseudo
if __name__=='__main__':
	threshold=beltWidth-minParcelWidth
	camera=picamera.PiCamera() #camera is camera,not to be changed!	
	time.sleep(2)
	exec(open("/home/pi/plausi_check/docs/camera_settings.txt"))
	#stream=io.BytesIO()
	global stream
	#stream = PiRGBArray(camera, (2592,1944))
	stream = PiRGBArray(camera)
	detected=False
	while True:
		try:
			distance=measureDistance(0)
			if distance-tolerance>=threshold:
				detected=False
			elif detected == False:	
				try:
					detected=True
					threads=[] 
					
					startTime=time.time()*1000
					q=True
					#threading.Thread(target=captureImage,args=()).start()
					capturedImage=captureImage(True)				
					#cv2.imshow('captured',capturedImage)					
					mirrorImage,labelImage=cropImage(capturedImage)
					#cv2.imshow("AfterCroppingMirror",mirrorImage)
					#cv2.imshow("AfterCroppingLabel",labelImage)
					labelImage=findLabel(labelImage)
					#cv2.imshow("AfterLabelSearch",labelImage)
					#cv2.waitKey(0)
					#key = cv2.waitKey(1) & 0xFF
 
					# if the `q` key is pressed, break from the lop
					#if key == ord("q"):
					#	break
					#scan('blank',mirrorImage)
					#scan('blank',labelImage)
					
					try:
						thread1=scanThread(1,'Mirror Scan',mirrorImage)
						thread2=scanThread(2,'Label Scan',labelImage)
						thread1.start()
						thread2.start()
						threads.append(thread1)
						threads.append(thread2)
						for t in threads:
							t.join()
					except Exception as exc:
						print exc
						logging.info(exc)
					
					print time.time()*1000-startTime
				except Exception as exc:
					print exc
					logging.info(exc)
			else:
				
				print 'I see a parcel but do nothing'
		except Exception as exc:	
				print exc
				logging.info(exc)
		time.sleep(distSensorPingRate)
