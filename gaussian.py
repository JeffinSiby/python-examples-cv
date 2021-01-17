#####################################################################

# Example :  gaussian smoothing for a a video file specified on the
# command line (e.g. python FILE.py video_file) or from an
# attached web camera with selectable opencl acceleration

# Author : Toby Breckon, toby.breckon@durham.ac.uk

# Copyright (c) 2021 Dept Computer Science,
#                    Durham University, UK
# License : LGPL - http://www.gnu.org/licenses/lgpl.html

#####################################################################

import cv2
import argparse
import sys
import math

#####################################################################

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
    "-ocl",
    "--opencl",
    action='store_true',
    help="enable opencl hardware acceleration")
parser.add_argument(
    'video_file',
    metavar='video_file',
    type=str,
    nargs='?',
    help='specify optional video file')

args = parser.parse_args()

#####################################################################

# this function is called as a call-back everytime the trackbar is moved
# (here we just do nothing)


def nothing(x):
    pass


#####################################################################

# define video capture object

try:
    # to use a non-buffered camera stream (via a separate thread)

    if not(args.video_file):
        import camera_stream
        cap = camera_stream.CameraVideoStream(use_tapi=args.opencl)
    else:
        cap = cv2.VideoCapture()  # not needed for video files

except BaseException:
    # if not then just use OpenCV default

    print("INFO: camera_stream class not found - camera input may be buffered")
    cap = cv2.VideoCapture()

# define display window name

window_name = "Live Camera Input"  # window name
window_name2 = "Gaussian Smoothing"  # window name

# setup OpenCL if specified on command line only

cv2.ocl.setUseOpenCL(args.opencl)

# if command line arguments are provided try to read video_name
# otherwise default to capture from attached H/W camera

if (((args.video_file) and (cap.open(str(args.video_file))))
        or (cap.open(args.camera_to_use))):

    # create window by name (as resizable)

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.namedWindow(window_name2, cv2.WINDOW_NORMAL)

    # add some track bar controllers for settings

    smoothing_neighbourhood = 3
    cv2.createTrackbar(
        "kernel size",
        window_name2,
        smoothing_neighbourhood,
        250,
        nothing)

    while (keep_processing):

        # start a timer (to see how long processing and display takes)

        start_t = cv2.getTickCount()

        # if video file successfully open then read frame from video

        if (cap.isOpened):
            ret, frame = cap.read()  # rescale if specified

            # when we reach the end of the video (file) exit cleanly

            if (ret == 0):
                keep_processing = False
                continue

            # rescale if specified

            if (args.rescale != 1.0):
                frame = cv2.resize(
                    frame, (0, 0), fx=args.rescale, fy=args.rescale)

        # get parameters from track bars

        smoothing_neighbourhood = cv2.getTrackbarPos("kernel size", window_name2)

        # check neighbourhood is greater than 3 and odd

        smoothing_neighbourhood = max(3, smoothing_neighbourhood)
        if not(smoothing_neighbourhood % 2):
            smoothing_neighbourhood = smoothing_neighbourhood + 1

        # performing smoothing on the image using a 5x5 smoothing mark (see
        # manual entry for GaussianBlur())

        smoothed = cv2.GaussianBlur(frame, (smoothing_neighbourhood,
                                    smoothing_neighbourhood), 0)

        # stop the timer and convert to ms. (to see how long processing and
        # display takes)

        stop_t = ((cv2.getTickCount() - start_t) /
                  cv2.getTickFrequency()) * 1000

        label = ('Processing time: %.2f ms' % stop_t) + \
            (' (Framerate: %.2f fps' % (1000 / stop_t)) + ')'
        cv2.putText(smoothed, label, (0, 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255))

        # display image

        cv2.imshow(window_name, frame)
        cv2.imshow(window_name2, smoothed)

        # start the event loop - essential

        # cv2.waitKey() is a keyboard binding function (argument is the time in
        # milliseconds). It waits for specified milliseconds for any keyboard
        # event. If you press any key in that time, the program continues.
        # If 0 is passed, it waits indefinitely for a key stroke.
        # (bitwise and with 0xFF to extract least significant byte of
        # multi-byte response)

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
            cv2.setWindowProperty(
                window_name2,
                cv2.WND_PROP_FULLSCREEN,
                cv2.WINDOW_FULLSCREEN)

    # close all windows

    cv2.destroyAllWindows()

else:
    print("No video file specified or camera connected.")

#####################################################################
