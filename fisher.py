import pyautogui
import time
import numpy as np
import cv2
import os


class Fisher(object):
    """catches and releases bobbers."""
    def __init__(self, size, position, io, reset_time):
        self.size = size
        self.position = position
        self.bobber = False
        self.fish = False
        self.poslist = []
        self.center = None
        self.curpos = None
        self.lastpos = None
        self.frame = None
        self.mask = None
        self.stack = None
        self.io = io
        self.counter = 0
        self.reset_time = reset_time
        self.timelist = []
        self.now = False

        ##
        self.BAIT_LOCATION = [713, 971]
        self.ACTION_BUTTON = [344, 966]
        self.REBUFF_COUNT = 100

        self.DISTANCE_THRESHOLD = 2
        self.KERNEL_SIZE = [11, 11]

        self.FRAME_X_MIN = 300
        self.FRAME_X_MAX = 450
        self.FRAME_Y_MIN = 400
        self.FRAME_Y_MAX = 700


    def prepare(self):
        pass
        #1. adjustcamera angle
        #2. fully zoom in

    def check_reset_time(self):
        """
        restarts the process if there has not been a catcher after x minutes
        """
        if self.now == False:
            self.now = time.time()
        if self.now + self.reset_time < time.time():
            print("safety restart")
            self.now = False
            pyautogui.moveTo(x=self.ACTION_BUTTON[0], y=self.ACTION_BUTTON[1], duration=1)
            pyautogui.click(button='left')
            time.sleep(1)


    def main(self):
        pass
        """
        filters the image for the ROI and decides if a catch has happened
        """
        #Prepare image for further data analysis
        self.frame = pyautogui.screenshot()
        self.frame = np.array(self.frame)
        self.frame = self.frame[self.FRAME_X_MIN:self.FRAME_X_MAX, self.FRAME_Y_MIN:self.FRAME_Y_MAX] #defines location of roi
        self.frame = cv2.GaussianBlur(self.frame, (self.KERNEL_SIZE[0], self.KERNEL_SIZE[1]), 0) #smoothen the image to remove artifacts
        hsv = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)
        self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)



        #Area specific filters - set this according to the object to filter out
        hsv_lower_red = np.array([90,90, 40]) 
        hsv_upper_red = np.array([180, 165,150]) 
 
        
        self.mask = cv2.inRange(hsv, hsv_lower_red, hsv_upper_red)
        self.mask = cv2.erode(self.mask, None, iterations=2) #remove remaining artifacts
        self.mask = cv2.dilate(self.mask, None, iterations=2) #preparation for center of mass calculation
        res = cv2.bitwise_and(self.frame, self.frame, mask=self.mask)

        _, contours, hierarchy = cv2.findContours(self.mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(self.frame, contours, -1, (0, 255, 0), 3)


        #calculates center of mass and checks distance towards last location
        if len(contours) > 0:
            self.bobber = True
            c = max(contours, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            self.center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

            cv2.circle(self.frame, self.center, 5, (0, 0, 255), -1)
            if self.io == True:
                print("center at: {}".format(self.center))

            if len(self.poslist) < 5:
                self.poslist.append(self.center)
                if self.io == True:
                    print(len(self.poslist))
            else:
                posdif = self.poslist[4][1] - self.poslist[3][1]
                self.poslist[3] = self.poslist[4]
                self.poslist[4] = self.center

                if self.io == True:
                    print("posdif", np.abs(posdif))

                if np.abs(posdif) > self.DISTANCE_THRESHOLD:
                    if self.io == True:
                        print("!!!!!fish found!!!!")
                    self.fish = True
                    self.counter = self.counter + 1

                    #After x amount of catches reapply buff
                    if self.counter > self.REBUFF_COUNT:
                        pyautogui.moveTo(x=self.BAIT_LOCATION[0], y=self.BAIT_LOCATION[1], duration=0.1)
                        pyautogui.click(button='left')
                        time.sleep(1)
                        self.counter = 0



        self.stack = np.vstack((self.frame, hsv, res))

    def catch(self):
        if self.bobber and self.fish == True:
            if self.io == True:
                print("initiating catch")

            pyautogui.moveTo(x=self.center[0] + self.FRAME_Y_MIN, y=self.center[1] + self.FRAME_X_MIN, duration=1)
            pyautogui.click(button='right')
            time.sleep(2)
            pyautogui.moveTo(x=self.ACTION_BUTTON[0], y=self.ACTION_BUTTON[1], duration=1)
            pyautogui.click(button='left')
            time.sleep(2)
        else:
            pass


    def reset(self):
        if self.bobber and self.fish == True:
            self.bobber = False
            self.fish = False
            self.poslist = []
            self.center = None
            self.curpos = None
            self.lastpos = None
            if self.io == True:
                print("resetting to: fish{} and bobber{}".format(self.fish, self.bobber))
        else:
            pass

if __name__ == "__main__":
    time.sleep(5)
    curr_pos = pyautogui.position()


    player = Fisher(size=5, position=curr_pos, io=True, reset_time=600)

    while (True):
        player.prepare()
        player.check_reset_time()
        player.main()
        player.catch()
        player.reset()

        time.sleep(0.1)
        if player.io == True:
            cv2.imshow('img', player.stack)
            cv2.imshow("mask", player.mask)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break