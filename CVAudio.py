from collections import deque
import numpy as np
import argparse
import imutils
import cv2
import PicAud as p

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video",
                help="path to the (optional) video file")
ap.add_argument("-b", "--buffer", type=int, default=32,
                help="max buffer size")
ap.add_argument("-i", "--image", help="Path to an image file")
args = vars(ap.parse_args())

# Define the Color range we are tracking
greenLower = (29, 86, 6)
greenUpper = (64, 255, 255)

# Set up variables
pts = deque(maxlen=args["buffer"])
counter = 0
(dX, dY) = (0, 0)
direction = ""

# run image program if flag used
if args.get("image", False):
    p.picToAud(cv2.imread(args["image"]))
    exit(0)

# If video supplied, use video, otherwise use webcam
if not args.get("video", False):
    camera = cv2.VideoCapture(0)
else:
    camera = cv2.VideoCapture(args["video"])


while 1:
    # Get first frame
    grab, frame = camera.read()
    if args.get("video") and not grab:
        break

    # make frame smaller, in the right direction, and in the right color space
    frame = imutils.resize(frame, width=800)
    cv2.flip(frame, 1, frame)
    blur = cv2.GaussianBlur(frame, (11, 11), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Highlight the green objects
    mask = cv2.inRange(hsv, greenLower, greenUpper)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    # select the green object
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    center = None

    # Draw circle around object
    if len(cnts) > 0:
        c = max(cnts, key=cv2.contourArea)
        (x, y), radius = cv2.minEnclosingCircle(c)
        M = cv2.moments(c)

        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

        print(center)

        if radius > 10:
            cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
            cv2.circle(frame, center, 5, (0, 0, 255), -1)
            pts.appendleft(center)

    # figure out movement direction
    for i in np.arange(1,len(pts)):
        if pts[i - 1] is None or pts[i] is None:
            continue
        if counter >= 10 and i == 1 and pts[-10] is not None:
            dX = pts[-10][0] - pts[i][0]
            dY = pts[-10][1] - pts[i][1]
            dirX, dirY = ("", "")

            if np.abs(dX) > 20:
                dirX = "West" if np.sign(dX) == 1 else "East"
            if np.abs(dY) > 20:
                dirY = "North" if np.sign(dY) == 1 else "South"
            if dirX != "" and dirY != "":
                direction = "{}-{}".format(dirY, dirX)
            else:
                direction = dirX if dirX != "" else dirY
        thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 2.5)
        cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)

    # Write text on the screen
    cv2.putText(frame, direction, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.65, (0, 0, 255), 3)
    cv2.putText(frame, "dx: {}, dy: {}".format(dX, dY),
                (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
                0.35, (0, 0, 255), 1)

    # Show frame
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF
    counter += 1

    if key == ord("q"):
        break


# Cleanup
camera.release()
cv2.destroyAllWindows()