import math
from flask1 import app
from flask import render_template,Response,redirect,url_for,request,flash
import cv2
import time
import numpy as np
import handtracking_module as htm
import time
import autopy
import mouse

from ctypes import POINTER, cast, pointer
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities
from pycaw.pycaw import IAudioEndpointVolume
# import ai_mouse


def generate_frames():
    cap=cv2.VideoCapture(0)
    width, height=640,480
    cap.set(3,width)
    cap.set(4, height)

    smooth = 5
    prevx, prevy= 0,0
    currx, curry=0,0
    detector = htm.Detection(maxHands=1)
    ptime=0
    frameR = 100 # frame reduction
    screen_w, screen_h = autopy.screen.size()


    # Volume control initialization and variables declaration 

    devices=AudioUtilities.GetSpeakers()
    interface=devices.Activate(IAudioEndpointVolume._iid_,CLSCTX_ALL,None)
    volume=cast(interface,POINTER(IAudioEndpointVolume))
    #volume.GetMute()
    #volume.GetMasterVolumeLevel()
    volRange=volume.GetVolumeRange()
    minVol=volRange[0]
    maxVol=volRange[1]
    vol=0
    volBar=400
    volPer=0

    while True:
        success,frame=cap.read()
        if not success:
            break
        else:
            success, img=cap.read()
            img = detector.findHands(img)
            lmList, bbox = detector.findPosition(img)
            #2
            if len(lmList)!=0:
                x1,y1=lmList[8][1:]
                x2,y2=lmList[12][1:]

                
                x3,y3=lmList[4][1],lmList[4][2]
                x4,y4=lmList[8][1],lmList[8][2]

                vlength=math.hypot(x4-x3,y4-y3)
                #3 
                fingers=detector.fingersUp()
                print(fingers)
                cv2.rectangle(img,(frameR,frameR),(width-frameR,height-frameR),(255,0,255),2)
                #4 only index finger:  moving move
                if fingers[1]==1 and fingers[2]==0 and fingers[0]==0 :

                    #5 convert coordinates
                    
                    x3=np.interp(x1, (frameR,width-frameR),(0,screen_w))
                    y3=np.interp(y1, (frameR,height-frameR),(0,screen_h))

                    currx=prevx+(x3-prevx)/smooth
                    curry=prevy+(y3-prevy)/smooth
                    autopy.mouse.move(screen_w-currx,curry)
                    # scale = autopy.screen.scale()
                    # autopy.mouse.smooth_move((screen_w-x3)/scale,(screen_h-y3)/scale)

                    cv2.circle(img,(x1,y1),15,(255,0,255),cv2.FILLED)
                    prevx, prevy = currx, curry

                # both index and middle fingers are up: clicking mode
                if fingers[1]==1 and fingers[2]==1 and fingers[3]==0:
                    length, img, infoline = detector.findDistance(8,12,img)
                    # print(length)
                    if length<40:
                        cv2.circle(img,(infoline[4],infoline[5]),15,(0,255,0),cv2.FILLED)
                        autopy.mouse.click()

                if fingers[1]==1 and fingers[2]==1 and fingers[3]==1:
                    length, img, infoline = detector.findDistance(8,12,img)
                    print(length)
                    if length<40:
                        cv2.circle(img,(infoline[4],infoline[5]),15,(0,255,0),cv2.FILLED)
                        autopy.mouse.click()
                        mouse.click('right')
                
                # volumn control function
                if fingers[0]==1 and fingers[1]==1:

                    vol=np.interp(vlength,[50,300],[minVol,maxVol])
                    volBar=np.interp(vlength,[50,300],[400,150])                 #shows a rectangle for volume
                    volPer=np.interp(vlength,[50,300],[0,100])                   #shows the volume in percentage according to distance

                    print(int(vlength),vol)
                    volume.SetMasterVolumeLevel(vol, None)

                
                                
            #11
            ctime = time.time()
            fps=1/(ctime-ptime)
            ptime=ctime
            # cv2.putText(
            #     img, str(int(fps)),
            #     (20,50),
            #     cv2.FONT_HERSHEY_PLAIN,
            #     3,(255,9,6), 3
            #     )

            #12
            # cv2.imshow("img",img)
            cv2.waitKey(1)

            ret,buffer=cv2.imencode('.jpg',frame)
            frame=buffer.tobytes()

        yield(b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/active')
def active():
    return render_template("active.html")
    
@app.route('/video')
def video():
    # ai_mouse.aiFunct()
    # return render_template("index.html")
    return Response(generate_frames(),mimetype='multipart/x-mixed-replace; boundary=frame')
       