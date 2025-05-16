import numpy as np
import cv2

frame = None
trackerPoints = []
inputMode = False

def main():
    global frame, trackerPoints, inputMode
    boundingBox = None
    trackerHistory = None

    # Get camera
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("Cant open camera")
        return

    # Name the window "Object Tracker"
    cv2.namedWindow("Object Tracker")

    # Call the function when mouse is clicked
    cv2.setMouseCallback("Object Tracker", selectTrackerPoints)

    # When to terminate
    termination = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
    

    # Loop through frames
    while True:
        # Current frame (and whether it was captured or not)
        was_frame_captured, frame = camera.read()

        # Error capturing frame
        if not was_frame_captured:
            break
            
        # If we have a bounding box
        if boundingBox is not None:

            # Add gaussian blur
            blurred = cv2.GaussianBlur(frame, (5, 5), 0)

            # Convert to Hue, Saturation, Value
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

            # Mask
            mask = cv2.inRange(hsv, np.array((0, 30, 32)), np.array((180, 255, 255)))

            # Image is the hsv, [0] - selects hue and saturation (from hsv), trackerHistory - histogram, range of pixels, scale
            backProjection = cv2.calcBackProject([hsv], [0, 1], trackerHistory, [0, 180, 0, 256], 1)

            # Keep relevant areas
            backProjection &= mask

            # Estimation has position, size and orientation and TrackerBox updates to the new estimation
            estimation, boundingBox = cv2.CamShift(backProjection, boundingBox, termination)

            # Get the points using numpy
            points = np.intp(cv2.boxPoints(estimation))

            # Draw the tracking "rectangle"
            cv2.polylines(frame, [points], True, (0, 255, 0), 2)

        # Add text
        cv2.putText(frame, "Press 'i' to select object | Press 'q' to quit", 
            (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 
            0.5, (0, 0, 0), 1)

        # Update the frame (every tick)
        cv2.imshow("Object Tracker", frame)

        # Get the key (padd with ff)
        key = cv2.waitKey(1) & 0xff

        # WaitKey() gives int value and ord() converts "i" to int value
        if key == ord("i"):
            # Reset trackerPoints
            trackerPoints = []
            
            inputMode = True

            # Exit loop when all trackerPoints are selected
            while len(trackerPoints) < 4:
                cv2.imshow("Object Tracker", frame)
                # Be able to exit even while selecting
                if cv2.waitKey(1) == ord("q"):
                    break
                

            
        
        elif inputMode and len(trackerPoints) == 4:
            # Get top left and bottom right points 
            trackerPoints = np.array(trackerPoints)
            # Sum x and y
            pointSum = trackerPoints.sum(axis=1)

            # Get min and max for top left and bottom right
            x_min = np.min(trackerPoints[:, 0])
            x_max = np.max(trackerPoints[:, 0])
            y_min = np.min(trackerPoints[:, 1])
            y_max = np.max(trackerPoints[:, 1])

            frame_copy = frame.copy()

            # Grab the object frame
            objFrame = frame_copy[y_min:y_max, x_min:x_max]
            objFrame = cv2.cvtColor(objFrame, cv2.COLOR_BGR2HSV)

            # Create a mask (doesnt include dark or unsaturated pixels)
            mask = cv2.inRange(objFrame, np.array((0, 30, 32)), np.array((180, 255, 255)))

            # Get a historigram for the object
            # Use hue and saturation
            trackerHistory = cv2.calcHist([objFrame], [0, 1], None, [32, 32], [0, 180, 0, 256])
            trackerHistory = cv2.normalize(trackerHistory, trackerHistory, 0, 255, cv2.NORM_MINMAX)
            boundingBox = (x_min, y_min, x_max - x_min, y_max - y_min)

            inputMode = False

        # Exit loop (program)
        elif key == ord("q"):
            break

    # Close the program
    camera.release()
    cv2.destroyAllWindows()

            


def selectTrackerPoints(event, x, y, flags, param):
    global frame, trackerPoints, inputMode
    
    # We are in selecting mode, the event was a click and we didnt select all points
    if inputMode and event == cv2.EVENT_LBUTTONDBLCLK and len(trackerPoints) < 4:
        # Add the point coords to the list
        trackerPoints.append((x, y))

        # Add a circle to the (x,y) coords, radius of 4, green and tickness of 2
        cv2.circle(frame, (x, y), 4, (0, 255, 0), 2)

        # Update frame
        cv2.imshow("Object Tracker", frame)


if __name__ == "__main__":
    main()
    