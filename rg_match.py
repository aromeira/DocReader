import cv2
import numpy as np
import pytesseract

try:
    import Image
except ImportError:
    from PIL import Image
from itertools import cycle,groupby
import subprocess
import pprint
from datetime import datetime

import sys

reload(sys)
sys.setdefaultencoding('utf8')

path_aux = "/home/danielle/projects/python/pyParseDocts/pieces/"


def find_corner(img,pos='top_right',doc=False):

    large_image = img
    #large_image.astype(np.float32)

    large_image = cv2.cvtColor(large_image,cv2.COLOR_BGR2GRAY)

    display = np.array(img,copy=True)


    for i in range(1,34):
        small_image = cv2.imread(path_aux + 'img_%d.jpg' % (i),1)

        small_image = cv2.cvtColor(small_image,cv2.COLOR_BGR2GRAY)

        img_name = 'img_%d.jpg' % (i)

        print(img_name)

        #small_image.astype(np.float32)

        import random
        rcolor = lambda: (random.randint(0,255),random.randint(0,255),random.randint(0,255))
        randomColor = rcolor()

        ## NOTA ! ! ! ! Aparentemente, o segredo para um bom patch, esta em recortar bem rente a linha esquerda para
        #               conseguir pegar ainda os que enconstam no canto e tambem recortar abaixo da curva pegando um
        #               pouco mais para fora do campo e tambem uma area maior dentro da propria linha do campo
        #               para que nao se confunda com letras O 0, C etc

        method = cv2.TM_CCOEFF_NORMED

        # print large_image.dtype
        # print small_image.dtype

        result = cv2.matchTemplate(small_image,large_image,method)
        # print result

        # We want the minimum squared difference
        # mn,_,mnLoc,_ = cv2.minMaxLoc(result)

        h,w = small_image.shape
        threshold = .8

        loc = np.where(result >= threshold)

        colsAndRows = []
        for pt in zip(*loc[::-1]):  # Switch collumns and rows

            print pt
            cv2.rectangle(display,pt,(pt[0] + w,pt[1] + h),randomColor,2)
            colsAndRows.append(pt)

        # Display the original image with the rectangle around the match.
        # cv2.imshow('output',display)
        # cv2.waitKey(0)

        # The image is only displayed if we call this

        #CUIDADO
        #cv2.imwrite(path_aux + img_name, display)

    return [display,colsAndRows]


def processa_rg(img):
    # img = scipy.ndimage.interpolation.rotate(img,270.0)
    # img = cv2.resize (img,(612,816))
    # img = cv2.resize (img,(557,372))

    # img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

    img_display,top_left_colsAndRows = find_corner(img)
    # cv2.imshow('titulo',img_display)

    time = str(datetime.now())
    cv2.imwrite(path_aux + "titulo" + time + ".jpg",img_display)



if __name__ == "__main__":

    for i in range(1,7):
        img = cv2.imread(path_aux + 'rg_%d.jpg' % (i),1)

        print ("Processando: rg_%d.jpg\n" % (i))

        processa_rg(img)

        print ("\n--------------------------------------------------------------------\n")
