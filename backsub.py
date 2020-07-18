import numpy as np
import cv2 as cv
from subprocess import Popen, PIPE, DEVNULL
from PIL import Image

'''
    PARAMETERS
'''
indev = 2 # opencv index for the chosen webcam
outdev = '/dev/video10' # virtual webcam from v4l2loopback module
resfps = [640, 480, 30] # resolution and fps for both input and output
chromakey = [0, 255, 0] # color for the new background in BGR
#
dilate_size = 10 # number of pixels to dilate the mask before blur
threshold_min = 5 # level to make the mask binary
mblur = 31 # median blur to elimante noise from the mask
gblur = 51 # gaussian blur to make the mask edges smooth


'''
    OPEN VIDEO CAPTURE DEVICE AND SET ITS RESOLUTION AND FPS
'''
cap = cv.VideoCapture(indev)
cap.set(cv.CAP_PROP_FRAME_WIDTH, resfps[0])
cap.set(cv.CAP_PROP_FRAME_HEIGHT, resfps[1])
cap.set(cv.CAP_PROP_FPS, resfps[2])

'''
    OPEN A PIPE WITH ffmpeg TO THE VIRTUAL WEBCAM, e.g. /dev/video10
    USE v4l2loopback MODULE TO CREATE THE VIRTUAL DEVICE FIRST
        install:
            https://github.com/umlaeute/v4l2loopback
        load as:
            sudo modprobe v4l2loopback video_nr=10
'''
out = Popen(['ffmpeg', '-y', '-i', '-', '-pix_fmt', 'yuyv422', '-f', 'v4l2', outdev], stdin=PIPE, stdout=DEVNULL, stderr=DEVNULL)


'''
    INIT DILATE GAUSSIAN KERNEL
'''
kernel = np.ones((dilate_size, dilate_size), np.uint8)
gauss = cv.getGaussianKernel(dilate_size, 0)
gauss = gauss * gauss.transpose(1, 0)


'''
    LOOP FOR READING AND MANIPULATING THE WEBCAM
'''
# first image as background
# can be changed later by pressing 'c'
ret, back = cap.read() 
# loop until key 'q' is pressed
while(True): 
    # read a frame
    ret, frame = cap.read() 

    # define mask by subtracking reference frame 'back'
    mask = cv.absdiff(frame, back)
    mask = cv.cvtColor(mask, cv.COLOR_BGR2GRAY) # convert to grayscale
    # threshold to make the mask binary
    # a better threshold would improve the code a lot!
    ret, mask = cv.threshold(mask, threshold_min, 255, 0) 
    
    # apply gaussian blur to the mask to eliminate some noise
    mask = cv.medianBlur(mask, mblur)
    mask = cv.dilate(mask, kernel)
    mask = cv.GaussianBlur(mask, (gblur, gblur), 0)
        
    # apply mask and save each component
    mask = mask / 255
    f0 = frame[:,:,0] * mask
    f1 = frame[:,:,1] * mask
    f2 = frame[:,:,2] * mask
    # change color by adding its complement
    f0 += (1-mask)*chromakey[0]
    f1 += (1-mask)*chromakey[1]
    f2 += (1-mask)*chromakey[2]
    # save back to frame
    frame[:,:,0] = f0
    frame[:,:,1] = f1
    frame[:,:,2] = f2
    
    # show result on opencv window 
    # must stay open so we can press 'c' to update background photo
    cv.imshow('cam', frame)
    
    # pipe result to ffmpeg
    frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    frame = Image.fromarray(np.uint8(frame))
    frame.save(out.stdin, 'JPEG')
    
    # check key
    keypressed = cv.waitKey(1)
    if keypressed == ord('q'):
        # quit if press q
        break
    elif keypressed == ord('c'):
        # update background picture if press 'c'
        ret, back = cap.read() 
#-------------------------------------------------------------------
# loop end
#-------------------------------------------------------------------

# close all devices
cap.release()
cv.destroyAllWindows()
out.stdin.close()
out.wait()


