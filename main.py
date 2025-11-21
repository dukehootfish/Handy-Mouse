import mediapipe as mp
import wx
import numpy as np
import cv2
from pynput.mouse import Button,Controller

draw = mp.solutions.drawing_utils
handSolution = mp.solutions.hands
hands = handSolution.Hands()
videoCap = cv2.VideoCapture(0)
thumbIDX = 4
indexIDX = 8

followIDX = 5

videoCap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
videoCap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

mouse = Controller()
app = wx.App(False)
(sx, sy) = wx.GetDisplaySize()

mouse_location = np.array([0,0])
previous_mouse_location = np.array([0,0])
pressed = False

def is_stable_movement(true_loc, virtual_loc, threshold=10):
    
    distance = np.linalg.norm(true_loc - virtual_loc)
    return distance > threshold

while True:
    success, img = videoCap.read()
    if success:
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        recHands = hands.process(imgRGB)
        if recHands.multi_hand_landmarks: 
            
            hand= recHands.multi_hand_landmarks[0]
            draw.draw_landmarks(img, hand, handSolution.HAND_CONNECTIONS)

            h, w = img.shape[:2]
            lm = hand.landmark
            x, y = int(lm[followIDX].x * w), int(lm[followIDX].y * h)
            cv2.circle(img, (x, y), 7, (255, 0, 0), cv2.FILLED)
            true_mouse_location = previous_mouse_location + ((int(x),int(y)) - previous_mouse_location)
            if 'mouse_location' not in locals():
                mouse_location = true_mouse_location
            if is_stable_movement(true_mouse_location, mouse_location):
                print("Moving Mouse")
                mouse_location = true_mouse_location
            mouse.position = (sx-(mouse_location[0]*sx/1200),mouse_location[1]*sy/675)
            previous_mouse_location = mouse_location
            thumb_x,thumb_y = int(lm[thumbIDX].x * w), int(lm[thumbIDX].y * h)
            index_x, index_y = int(lm[indexIDX].x * w), int(lm[indexIDX].y * h)
            distance = np.hypot(index_x - thumb_x, index_y - thumb_y)
            cv2.line(img, (thumb_x, thumb_y), (index_x, index_y), (255, 0, 255), 2)
            cv2.putText(img, f'Distance: {int(distance)}', (40, 450), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
            if(distance < 40 and not pressed):
                #print("Click")
                mouse.press(Button.left)
                pressed = True
            elif(distance >= 40):
                #print("Unclick")
                mouse.release(Button.left)
                pressed = False

    cv2.imshow("CamOutput", img)
    cv2.waitKey(1)

