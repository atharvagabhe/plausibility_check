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
import getch
from picamera.array import PiRGBArray


#2.Declarations
#initialisation camera duh!!!
camera=picamera.PiCamera() #camera is camera,not to be changed!
time.sleep(2)
exec(open("/home/pi/plausi_check/settings/camera_settings.txt"))
#configuration inistialisation
Config=ConfigParser.ConfigParser()
Config.read("../settings/settings.ini")
#serial peri peri interface insitialisation,might go away after lichtschrank is tested!
spi = spidev.SpiDev()
spi.open(0,0)

logging.basicConfig(filename='../logs/plausicheck.log',filemode='w',level=logging.DEBUG)

#all the base moved here against the war on global variables was lost
parser=argparse.ArgumentParser()
#the thing about argparse is that it is extremely easy and difficult at the same time!!
parser.add_argument('-i','--image',dest="filename",help='*insert your mama joke',metavar="FILE")
parser.add_argument('-k','--key',type=str,help='Select key to trigger script trigger')
parser.add_argument('-c','--contrast',type=int,help='adjust contrast on connected image capturing device,lovingly known as a camera')
parser.add_argument('-br','--brightness',type=int,help='na na na na na na ')
parser.add_argument('-sh','--shutterspeed',type=int,help=' speed of shutting up')
parser.add_argument('-iso','--ISO',type=int,help='international standards organisation,jk :P')
parser.add_argument('-res','--resolution',type=int,help='like New Years')
parser.add_argument('-set','--setup',required=False,help='unpossible',action="store_true")
#parser.add_argument('-e1','--image',required=False,help='*insert your mama joke',action="store_true")
#parser.add_argument('-e2','--image',required=False,help='*insert your mama joke',action="store_true")
args=parser.parse_args() 
PingRate=Config.getfloat("Delay","PingRate")
beltWidth=Config.getfloat("Belt","Width")##
minParcelWidth=Config.getfloat("Sensor","PacketWidth")#According to Holger's Table
contourLow=Config.getint("CV2","ContourLow")
contourHigh=Config.getint("CV2","ContourHigh")
ratio=Config.getint("Belt","Ratio")
xmax1 =Config.getint("Belt","Xmax")
ymax1 =Config.getint("Belt","Ymax")
threshold=beltWidth-minParcelWidth


threadflag1=False


class Detector():
	def __init__(self):
		self.channel = 0
		self.tolerance = 5 # 5 cm..
		self.triggerDistance = 30 # 30 cm 
		self.beltWidth = 54 # 54 cm
		self.detected = False
		self.loadConfig()				
		#set the variables static.. if file is found, change to file config
		
	def loadConfig(self):
		try:
			self.channel = Config.getint("ADC","Channel")		
			self.tolerance = Config.getfloat("Sensor","Tolerance")
			self.triggerDistance = Config.getfloat("Sensor","Trigger")
			self.beltWidth = Config.getfloat("Belt","Width")#
		except:
			print "file not found"	
			#file is not found...
						
	def measureDistance(self):		
		val = spi.xfer2([1,(8+self.channel)<<4,0])	
		data = ((val[1]&3) << 8) + val[2]	
		v=(data/1023.0)*3.3
		dist = 16.2537 * v**4 - 129.893 * v**3 + 382.268 * v**2 - 512.611 * v + 301.439
		return dist		
		
	def detectParcel(self):
		dist = self.measureDistance()  			
		#remove for production
		print "| Distance | %.2f cm" % dist  	
	
		if dist - self.tolerance <= self.triggerDistance and self.detected == False:
			self.detected=True
			return detected
			
		elif dist  + self.tolerance > self.beltWidth:		
			self.detected = False	
		
		#remove for production		
		if dist - self.tolerance <= self.triggerDistance and self.detected == True:
			print 'I should do nothing'	
		return False			
	


#4.Threads----------------------------combine all classes for thread handling 
# combine in 1 thread with an arugment for the type
class irThread(Thread):
    def __init__(self, threadID, name, event):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.event = event
        self.detector = Detector()        
        
    def run(self):
        print "Starting " + self.name
        while True:
			try:
				if args.key:
					char = getch.getch()
				#print char
				if (self.detector.detectParcel() or char == keyPress): #or keypress
					event.set()														
				time.sleep(PingRate)
				char = ""
			except Exception as exc:
				print 'Aborting::'
				print exc
				logging.info(exc)
        print "Exiting " + self.name		

class capdetThread(Thread):	
    def __init__(self, threadID, name, event):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.event = event
        
    def run(self):
		while True:
			try:
				event.wait(timeout=None)											
				captureDetectSequence()								
			except:
				print "Exiting with error" + self.name
			finally: event.clear()
		


#5..Function definitions

		
def captureImage(var):#take a picture;req1:take to cv obj. req2:format vis a vis image quality size and time required in each step		
	try:
		if var==False:
			image = cv2.imread('/home/pi/plausi_check/160523_recordings/brown.10.jpg')
		else:	
			stream=PiRGBArray(camera)			
			print "CaptureImage"
			
			stream1 = io.BytesIO()
			
			cvtime=time.time()*1000
			logging.info('clicktime')
			#logging.info(time.time()*1000-temp)			
								

			camera.capture(stream, format='bgr',use_video_port=True)			
			image=stream.array
			cv2.imwrite("/home/pi/plausi_check/TestImages/img_videoport_raw" + str(cvtime)+".jpg",image)
			#print sys.getsizeof(image)
			stream.truncate(0)

			camera.capture(stream, format='bgr')
			stream.seek(0)
			image2= stream.array
			cv2.imwrite("/home/pi/plausi_check/TestImages/img_stillport_raw" + str(cvtime)+".jpg",image2)
			
			camera.capture(stream1,format='jpeg', quality=100)								
			data=np.fromstring(stream1.getvalue(),dtype=np.uint8)
			image3=cv2.imdecode(data,1)			
			#image = stream.array
			cvtime=time.time()*1000-cvtime				
			logging.info(cvtime)					
			
			cv2.imwrite("/home/pi/plausi_check/TestImages/img_stillport_jpeg" + str(cvtime)+".jpg",image3)

			#should comment this out...
			
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
	mirror=rotateImage(mirror,1)
	cv2.imwrite("mirror.jpg",mirror)

	#label=img.copy()
	band = img[Config.getfloat("Belt","YLow"):Config.getfloat("Belt","YHigh"),Config.getfloat("Belt","XLow"):Config.getfloat("Belt","XHigh")]
	
	
	return mirror, band
	
	
	
def findLabel(img2):#should take an argument,output of captureImage()
	try:
		cv2.imwrite("label0.jpg",img2)
		newPoints=None
		img = cv2.resize(img2,(xmax1/ratio,ymax1/ratio))###
		cv2.imwrite("label.jpg",img)
		gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
		#ret,gray = cv2.threshold(gray,Config.getint("CV2","Threshold"),255,0) #old was 175 ###th--var
		ret,gray = cv2.threshold(gray,190,255,0) #old was 175 ###th--var
		
		_,contours,_= cv2.findContours(gray,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
		
		for cnt in contours:
			if contourLow<cv2.contourArea(cnt)<contourHigh:# thirty-thousand to hundred-thousand
				rect = cv2.minAreaRect(cnt) 
				points = cv2.boxPoints(rect)
				
				newPoints = ratio*np.array(points)		
				newPoints = np.int0(newPoints)
				#uncomment to see result
				cv2.drawContours(img2, [newPoints], -1, (0, 255, 0), 3)	
				#cv2.imwrite("cont.jpg", img2)
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
	print "angle is: "
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
		print "Exception in scan"
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
			cv2.imwrite("label2.jpg", labelImage)
			scan(mirrorImage)
			scan(labelImage)
		else:
			print 'No label found exiting.'
			#this shud call the scan function with the whole image
			
	except Exception as exc:		
		logging.info(exc)
	threadflag1=False		
	
def argumentParsing():	
	
	
	if args.filename!=None:
		im=cv2.imread(args.filename)
		scan(im)
		#print im.size
		#cv2.imshow("image",im)#i think it does display		
		#cv2.waitKey(0)
	if args.key:
		keyPress=args.key
		print keyPress+' is the selected key for simulating object detection'
		#print 'key'
	if args.contrast:
		camera.contrast=args.contrast
		print args.contrast
		print 'contrast'
	if args.brightness:
		camera.brightness=args.brightness
		print 'my eyes,my eyes'
	if args.ISO:
		print 'ISO'
	if args.setup:
		print 'setup'
	if args.shutterspeed:
		print 'wut?'	
	#sys.exit()	
	
#6.Main	
#pseudo
if __name__=='__main__':	
	try:
		argumentParsing()
		event = threading.Event()
		threadIR=irThread(1,'Distance Sensor Thread', event)	
		threadIR.start()
		threadCD=capdetThread(2,'Capture and Detect Thread', event)	
		threadCD.start()		
		
		
	except Exception as exc:	
			print exc
			logging.info(exc)
	time.sleep(PingRate)

