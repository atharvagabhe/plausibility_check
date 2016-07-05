import picamera
import io
import time
import cv2
import numpy as np

cam=picamera.PiCamera()
stream=io.BytesIO()
cam.resolution=(2592,1944)
time.sleep(2)
cam.start_recording('/dev/null',format='h264',resize=(640,480),splitter_port=1)
time.sleep(2)
print 'CP1'
cam.stop_recording()
cvtime=time.time()*1000
cam.capture(stream,format='jpeg', quality=100, use_video_port=True)					
data=np.fromstring(stream.getvalue(),dtype=np.uint8)
image=cv2.imdecode(data,1)			
cvtime=time.time()*1000-cvtime									
print cvtime
cv2.imwrite("/home/pi/plausi_check/TestImages/img_" + str(cvtime)+".jpg",image)
