import numpy as np
import argparse
import cv2
import time

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True, help="path to file")
args=vars(ap.parse_args())


#img processing

#print (time.time()*1000)
temp = time.time()*1000
image = cv2.imread(args["image"])

print (time.time()*1000 - temp)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#gray = cv2.cvtColor(image, cv2.COLOR_GRAY)
print (time.time()*1000 - temp)

gradX = cv2.Sobel(gray, ddepth = cv2.CV_32F, dx = 1, dy = 0, ksize= -1)
gradY = cv2.Sobel(gray, ddepth = cv2.CV_32F, dx = 0, dy = 1, ksize= -1)

gradient = cv2.subtract(gradX, gradY)
gradient = cv2.convertScaleAbs(gradient)

#cv2.imshow("Image", gradient)


blurred = cv2.blur(gradient, (10,10))
#cv2.imshow("Image", blurred)


(_, thresh) = cv2.threshold(blurred, 225, 255, cv2.THRESH_BINARY)

kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 60))


print (time.time()*1000 - temp)
#takes a lot of time!!!
closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

print (time.time()*1000 - temp)

#cv2.imshow("Image", closed)

#is this needed???
#closed = cv2.erode(closed, None, iterations = 4) 
#closed = cv2.dilate(closed, None, iterations = 4) 

#cv2.imshow("Image", closed)


(_, cnts,_)  = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
c = sorted (cnts, key = cv2.contourArea, reverse = True) [0]
rect = cv2.minAreaRect(c)
box = np.int0(cv2.boxPoints(rect))
print (time.time()*1000 - temp)

cv2.drawContours(image, [box], -1, (0,255,0),3)
cv2.imshow("Image", image)
cv2.waitKey(0)

