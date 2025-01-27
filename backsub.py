#!/usr/bin/env python3

# to init the virutal webcam run:
#   sudo modprobe v4l2loopback video_nr=10
# to play the stream preview run:
#   ffplay /dev/video10

import numpy as np
import cv2 as cv
import pyfakewebcam
from os.path import isfile

##############################################################################
# PARAMETERS
##############################################################################
# input  / output
indev = 2 # opencv index for the chosen webcam
outdev = '/dev/video10' # virtual webcam from v4l2loopback module
# replace background with: 'chromakey', 'blur', path to image
#howto = 'ImageTest640x480.JPG'
#howto = 'chromakey'
howto = 'blur'
# resolution, fps and color
resfps = [640, 480, 30] # resolution and fps for both input and output
chromakey = [0, 255, 0] # color for the new background in BGR
# kernel and threshold paramters
dilate_size = 5 # number of pixels to dilate the mask before blur
threshold_min = 10 # level to make the mask binary
mblur = 21 # median blur to eliminate noise from the mask
N_erode = 2 # number of times to erode the mask
N_dilate = 2 # number of times to dilate the mask
gblur = 21 # gaussian blur to make the mask edges smooth
gblur2 = 51 # gaussian blur to blur the background if howto='blur'


##############################################################################
# APPLY MASK TO REMOVE BACKGROUND OR REPLACE WITH IMAGE
#
# flipping index 0 and 2 
#    to avoid having to call cvtColor from BGR to RGB when calling
#    pyfakewebcam
##############################################################################
def how_to_apply_mask(howto):
    if howto == "chromakey":
        def applymask(frame, mask, newback):
            # newback is ignored in this case
            frame[:,:,1] = frame[:,:,1] * mask + (1-mask)*chromakey[1]
            frame[:,:,2], frame[:,:,0] = (frame[:,:,0] * mask + (1-mask)*chromakey[0],
                                          frame[:,:,2] * mask + (1-mask)*chromakey[2])
    elif howto == "blur" or isfile(howto):
        def applymask(frame, mask, newback):
            frame[:,:,1] = frame[:,:,1] * mask + (1-mask)*newback[:,:,1]
            frame[:,:,2], frame[:,:,0] = (frame[:,:,0] * mask + (1-mask)*newback[:,:,0],
                                          frame[:,:,2] * mask + (1-mask)*newback[:,:,2])
    return applymask
# set it up
applymask = how_to_apply_mask(howto)

##############################################################################
# GET MASK FROM FRAME AND BACKGROUND
##############################################################################
# aux kernels
kernel = np.ones((dilate_size, dilate_size), np.uint8)
gauss = cv.getGaussianKernel(dilate_size, 0)
gauss = gauss * gauss.transpose(1, 0)
# the function
def get_mask(frame, back):
    # define mask by subtracking reference frame 'back'
    mask = cv.cvtColor(cv.absdiff(frame, back), cv.COLOR_BGR2GRAY) # convert to grayscale
    # threshold to make the mask binary
    # a better threshold would improve the code a lot!
    ret, mask = cv.threshold(mask, threshold_min, 255, 0) 
    # apply gaussian blur to the mask to eliminate some noise
    mask = cv.medianBlur(mask, mblur)
    # erode and dilate back to eliminate small noise
    mask = cv.erode(mask, kernel, iterations=N_erode)
    mask = cv.dilate(mask, kernel, iterations=N_dilate)
    # gaussian blur to make the edges smooth
    mask = cv.GaussianBlur(mask, (gblur, gblur), 0)
    # apply mask to each component and change background
    mask = mask / 255
    #
    return mask

##############################################################################
# INIT INPUT AND OUTPUT DEVICES
##############################################################################
# input real webcam via openCV
cap = cv.VideoCapture(indev)
cap.set(cv.CAP_PROP_FRAME_WIDTH, resfps[0])
cap.set(cv.CAP_PROP_FRAME_HEIGHT, resfps[1])
cap.set(cv.CAP_PROP_FPS, resfps[2])
# output stream to virtual webcam with pyfakewebcam and v4l2loopback
out = pyfakewebcam.FakeWebcam(outdev, resfps[0], resfps[1])

##############################################################################
# HOW TO OUTPUT THE RESULT?
##############################################################################
def stream_it(frame):
    # stream to virtual device using pyfakewebcam
    # can be seen via ffplay /dev/video10
    #frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    out.schedule_frame(frame)    

##############################################################################
# MAIN LOOP FOR THE STREAMING
##############################################################################
# first image as background, can be changed later by pressing 'c'
ret, back = cap.read()
# set newback for replacement
if howto == "blur":
    newback = cv.GaussianBlur(back, (gblur2, gblur2), 0)
elif isfile(howto):
    newback = cv.imread(howto)
else:
    newback = None
# show captured background on opencv window
# we need this window to interact with keyboard
# but we don't need to keep the stream running there
cv.imshow('cam', back)
# ENTER THE LOOP
while(True): # loop until key 'q' is pressed

    # run some frames without check for key
    # to avoide the 1 ms delay
    for i in range(30):
        # read a frame
        ret, frame = cap.read() 
        # get the mask and apply in place
        mask = get_mask(frame, back)
        # and apply it to frame
        applymask(frame, mask, newback)
        # stream the result
        stream_it(frame)
    
    # check key
    keypressed = cv.waitKey(1)
    if keypressed == ord('q'):
        # quit if press q
        break
    elif keypressed == ord('c'):
        # update background picture if press 'c'
        ret, back = cap.read()
        # update image on opencv window
        cv.imshow('cam', back)
        if howto == "blur":
            newback = cv.GaussianBlur(back, (gblur2, gblur2), 0)

##############################################################################
# THE END, CLOSE ALL WINDOWS AND DEVICES
##############################################################################
cap.release()
cv.destroyAllWindows()

