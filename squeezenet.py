##########################################################################

# Example : perform live display of squeezenet CNN classification from a video
# file specified on the command line (e.g. python FILE.py video_file) or from
# an attached web camera

# Author : Toby Breckon, toby.breckon@durham.ac.uk

# Copyright (c) 2019 Toby Breckon, Engineering & Computing Science,
#                    Durham University, UK
# License : LGPL - http://www.gnu.org/licenses/lgpl.html

# Based heavily on the example provided at:
# https://github.com/opencv/opencv/blob/master/samples/dnn/classification.py

##########################################################################

# To use download the following files:

# https://raw.githubusercontent.com/opencv/opencv/master/samples/data/dnn/classification_classes_ILSVRC2012.txt
# -> classification_classes_ILSVRC2012.txt
# https://github.com/forresti/SqueezeNet/raw/master/SqueezeNet_v1.1/squeezenet_v1.1.caffemodel
# -> squeezenet_v1.1.caffemodel
# https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/dnn/squeezenet_v1.1.prototxt
# -> squeezenet_v1.1.prototxt

##########################################################################

import cv2
import argparse
import sys
import math
import numpy as np

##########################################################################
# dummy on trackbar callback function


def on_trackbar(val):
    return

##########################################################################


keep_processing = True

# parse command line arguments for camera ID or video file

parser = argparse.ArgumentParser(
    description='Perform ' +
    sys.argv[0] +
    ' example operation on incoming camera/video image')
parser.add_argument(
    "-c",
    "--camera_to_use",
    type=int,
    help="specify camera to use",
    default=0)
parser.add_argument(
    "-r",
    "--rescale",
    type=float,
    help="rescale image by this factor",
    default=1.0)
parser.add_argument(
    "-fs",
    "--fullscreen",
    action='store_true',
    help="run in full screen mode")
parser.add_argument(
    "-use",
    "--target",
    type=str,
    choices=['cpu', 'gpu', 'opencl'],
    help="select computational backend",
    default='cpu')
parser.add_argument(
    'video_file',
    metavar='video_file',
    type=str,
    nargs='?',
    help='specify optional video file')
args = parser.parse_args()

##########################################################################

# define video capture object

try:
    # to use a non-buffered camera stream (via a separate thread)

    if not(args.video_file):
        import camera_stream
        cap = camera_stream.CameraVideoStream()
    else:
        cap = cv2.VideoCapture()  # not needed for video files

except BaseException:
    # if not then just use OpenCV default

    print("INFO: camera_stream class not found - camera input may be buffered")
    cap = cv2.VideoCapture()

##########################################################################

# define display window name

window_name = "SqueezeNet Image Classification - Live"  # window name

# create window by name (as resizable)

cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
trackbarName = 'reporting confidence > (x 0.01)'
cv2.createTrackbar(trackbarName, window_name, 50, 100, on_trackbar)

##########################################################################

# Load names of class labels

classes = None
with open("classification_classes_ILSVRC2012.txt", 'rt') as f:
    classes = f.read().rstrip('\n').split('\n')

##########################################################################

# Load CNN model

net = cv2.dnn.readNet(
    "squeezenet_v1.1.caffemodel",
    "squeezenet_v1.1.prototxt",
    'caffe')

# set up compute target as one of [GPU, OpenCL, CPU]

if (args.target == 'gpu'):
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
elif (args.target == 'opencl'):
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_OPENCL)
else:
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

##########################################################################

# if command line arguments are provided try to read video_name
# otherwise default to capture from attached camera

if (((args.video_file) and (cap.open(str(args.video_file))))
        or (cap.open(args.camera_to_use))):

    while (keep_processing):

        # start a timer (to see how long processing and display takes)

        start_t = cv2.getTickCount()

        # if camera /video file successfully open then read frame

        if (cap.isOpened):
            ret, frame = cap.read()

            # when we reach the end of the video (file) exit cleanly

            if (ret == 0):
                keep_processing = False
                continue

            # rescale if specified

            if (args.rescale != 1.0):
                frame = cv2.resize(
                    frame, (0, 0), fx=args.rescale, fy=args.rescale)

        #######################################################################
        # squeezenet:
        #   model: "squeezenet_v1.1.caffemodel"
        #   config: "squeezenet_v1.1.prototxt"
        #   mean: [0, 0, 0]
        #   scale: 1.0
        #   width: 227
        #   height: 227
        #   rgb: false
        #   classes: "classification_classes_ILSVRC2012.txt
        #######################################################################

        # create a 4D tensor "blob" from a frame.

        blob = cv2.dnn.blobFromImage(
            frame, scalefactor=1.0, size=(
                227, 227), mean=[
                0, 0, 0], swapRB=False, crop=False)

        # Run forward inference on the model

        net.setInput(blob)
        out = net.forward()

        # get class label with a highest score from final softmax() layer

        out = out.flatten()
        classId = np.argmax(out)
        confidence = out[classId]

        # stop the timer and convert to ms. (to see how long processing takes

        stop_t = ((cv2.getTickCount() - start_t) /
                  cv2.getTickFrequency()) * 1000

        # Display efficiency information

        label = ('Inference time: %.2f ms' % stop_t) + \
            (' (Framerate: %.2f fps' % (1000 / stop_t)) + ')'
        cv2.putText(frame, label, (0, 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255))

        # get confidence threshold from track bar
        confThreshold = cv2.getTrackbarPos(trackbarName, window_name) / 100

        # if we are quite confidene about classification then dispplay
        if (confidence > confThreshold):
            # add predicted class.
            label = '%s: %.4f' % (
                classes[classId]
                if classes else 'Class #%d' % classId, confidence)
            cv2.putText(frame, label, (0, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255))

        # display image

        cv2.imshow(window_name, frame)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN,
                              cv2.WINDOW_FULLSCREEN & args.fullscreen)

        # start the event loop - essential

        # wait 40ms or less depending on processing time taken (i.e. 1000ms /
        # 25 fps = 40 ms)

        key = cv2.waitKey(max(2, 40 - int(math.ceil(stop_t)))) & 0xFF

        # It can also be set to detect specific key strokes by recording which
        # key is pressed

        # e.g. if user presses "x" then exit  / press "f" for fullscreen
        # display

        if (key == ord('x')):
            keep_processing = False
        elif (key == ord('f')):
            args.fullscreen = not(args.fullscreen)

    # close all windows

    cv2.destroyAllWindows()

else:
    print("No video file specified or camera connected.")

##########################################################################
