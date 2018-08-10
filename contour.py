import cv2
import numpy as np
import scipy.io
import scipy.misc
import scipy.ndimage
from datetime import datetime
import time
import os
import glob
from subprocess import call
import sys
import random
import math


try:
    import Image
except ImportError:
    from PIL import Image
import pytesseract
import pprint

reload(sys)
sys.setdefaultencoding('utf8')

path_aux = "/home/danielle/projects/python/pyParseDocts/img/"

if __name__ == "__main__":

    files = [path_aux + 'rg_daniela_app.jpg',
             path_aux + 'rg_heitor_app.jpg',
             path_aux + 'rg_juliana_app.jpg'
             ]

            #path_aux + 'rg_erica_app.jpg',
            #path_aux + 'rg_flavia_app.jpg',
            #path_aux + 'rg_daiane_3_app.jpg',
    for f in files:
        print "========================================="

        rg = cv2.imread(f,0)
        rg = cv2.resize(rg,(800,600))

        # rg = cv2.bitwise_not(rg,rg)

        ret,campo = cv2.threshold(rg,0,255,cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)


        # horizontalSize = 2
        # verticalSize   = 2
        # horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT,(horizontalSize,verticalSize))
        # print horizontalStructure
        # campo = cv2.dilate(campo,horizontalStructure,(-1,-1),iterations=2)

        kernel = np.ones((1,1),np.uint8)
        #campo = cv2.morphologyEx(campo,cv2.MORPH_CLOSE,kernel,iterations=3)
        campo = cv2.morphologyEx(campo,cv2.MORPH_CLOSE,kernel,iterations=2)

        kernel = np.ones((2,2),np.uint8)
        #campo = cv2.morphologyEx(campo,cv2.MORPH_OPEN,kernel,iterations=2)
        campo = cv2.morphologyEx(campo,cv2.MORPH_OPEN,kernel,iterations=3)

        time = str(datetime.now())
        cv2.imwrite(path_aux + "thresh" + time + ".jpg",campo)

        display = np.array(rg,copy=True)
        _, contours,hierarchy = cv2.findContours(campo,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

        print "Foram encontrados %d contornos" % (len(contours))

        for idx,cnt in enumerate(contours):
            x,y,w,h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)

            # f (area >= 40 and area <= 160) and (h >= 18 and h < 30 ):
            # if (h >= 18 and  h < 30 ):
            if (area > 20 and area < 250 and h >= 17 and h <= 100):
                cv2.rectangle(display,(x,y),(x + w,y + h),(255,255,255),2)
                print x,y,w,h,area,'*'

            print x,y,w,h,area

        time = str(datetime.now())
        cv2.imwrite(path_aux + "contornos" + time + ".jpg",display)
        # cv2.imshow('contornos',display)
        # cv2.waitKey(0)
        # teste2(rg)
        # teste3(rg)
