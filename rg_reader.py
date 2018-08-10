# -*- coding: utf-8 -*-

import cv2
import numpy as np
import scipy.io
import scipy.misc
import scipy.ndimage
import datetime
import time
import os
import glob
from subprocess import call
import sys
import random
import math
from string import digits
import pytesseract
import string
import datetime

import sys

from RG import RG

reload(sys)
sys.setdefaultencoding('utf8')

try:
    import Image
except ImportError:
    from PIL import Image

img_path = "/home/danielle/projects/python/pyParseDocts/img/"

LONGE_BORDA = 1
PERTO_BORDA = 2

doc_fields = {}
person_clr_range = {}

class RgReader:
    def __init__(self, doc_version,doc_side,doc_img):
        #self.doc_type = doc_type.upper()
        self.doc_version = doc_version
        self.doc_side = doc_side.upper()
        self.doc_img = doc_img

    def trata_campo(self,campo,tipo):
        try:
            print("CAMPO ANTES [%s]" % campo)

            if tipo == "DATA":

                if campo.find(" ") > 0:
                    campo = string.replace(campo," ","")

                if campo.find("'") > 0:
                    campo = string.replace(campo,"'","")

                if campo.find(",") > 0:
                    campo = string.replace(campo,",","")

                if campo.find("]") > 0:
                    campo = string.replace(campo,"]","/")

                if campo.find("[") > 0:
                    campo = string.replace(campo,"[","/")

                if campo.find("Cl") > 0:
                    campo = string.replace(campo,"Cl","01")

                if campo.find("JAN") > 0:
                    campo = string.replace(campo,"JAN","01")

                elif campo.find("JQN") > 0:
                    campo = string.replace(campo,"JQN","01")

                elif campo.find("FEV") > 0:
                    campo = string.replace(campo,"FEV","02")

                elif campo.find("FEU") > 0:
                    campo = string.replace(campo,"FEU","02")

                elif campo.find("MAR") > 0:
                    campo = string.replace(campo,"MAR","03")

                elif campo.find("ABR") > 0:
                    campo = string.replace(campo,"ABR","04")

                elif campo.find("MAI") > 0:
                    campo = string.replace(campo,"MAI","05")

                elif campo.find("JUN") > 0:
                    campo = string.replace(campo,"JUN","06")

                elif campo.find("JVN") > 0:
                    campo = string.replace(campo,"JVN","06")

                elif campo.find("JUL") > 0:
                    campo = string.replace(campo,"JUL","07")

                elif campo.find("JVL") > 0:
                    campo = string.replace(campo,"JVL","07")

                elif campo.find("AGO") > 0:
                    campo = string.replace(campo,"AGO","08")

                elif campo.find("SET") > 0:
                    campo = string.replace(campo,"SET","09")

                elif campo.find("OUT") > 0:
                    campo = string.replace(campo,"OUT","10")

                elif campo.find("NOV") > 0:
                    campo = string.replace(campo,"NOV","11")

                elif campo.find("DEZ") > 0:
                    campo = string.replace(campo,"DEZ","12")

                if len(campo) == 6:  # DDMMAA
                    campo = campo[:2] + "/" + campo[2:-2] + "/" + campo[-2:]

                if len(campo) == 8:
                    if campo.find("/") > 0:  # DD/MM/AA
                        aux = campo[-2:]

                        if aux > 30:
                            aux = "19" + aux
                        else:
                            aux = "20" + aux

                        campo = campo[:-2]

                        campo = ''.join((campo,aux))

                    else:  # DDMMAAAA
                        campo = campo[:2] + "/" + campo[2:-4] + "/" + campo[-4:]

                #verificar se no final dos tratamentos, foi gerada uma data valida
                if self.validateDate(campo) == False:
                    campo = ""


            elif tipo == "RG":

                if campo.find("?") > 0:
                    campo = string.replace(campo,"?","")

                if campo.find(" ") > 0:
                    campo = string.replace(campo," ","")

                if campo.find("l") > 0:
                    campo = string.replace(campo,"l","1")

                if campo.find("via") > 0:
                    campo = string.replace(campo,"via","")

                if campo.find("'") > 0:
                    campo = string.replace(campo,"'","")


            elif tipo == "NAT":

                if campo.find("SPA") > 0:
                    campo = string.replace(campo,"SPA","SÃO PA")

                if campo.find("S.PA") > 0:
                    campo = string.replace(campo,"S.PA","SÃO PA")

                if campo.find("()") > 0:
                    campo = string.replace(campo,"()","O")

                if campo.find(" ,") > 0:
                    campo = string.replace(campo," ,",",")

                if campo.find("'") > 0:
                    campo = string.replace(campo,"'","")


            elif tipo == "NOME":

                if campo.find("?") > 0:
                    campo = string.replace(campo,"?","")

                if campo.find("!") > 0:
                    campo = string.replace(campo,"!","")

                if campo.find(".") > 0:
                    campo = string.replace(campo,".","")

                if campo.find("“") > 0:
                    campo = string.replace(campo,"“","")

                if campo.find("‘") > 0:
                    campo = string.replace(campo,"‘","")

                if campo.find(",") > 0:
                    campo = string.replace(campo,",","")

                if campo.find(":") > 0:
                    campo = string.replace(campo,":","")

                if campo.find("\"") > 0:
                    campo = string.replace(campo,"\"","")

                if campo.find("/") > 0:
                    campo = string.replace(campo,"/","")

                if campo.find("(") > 0:
                    campo = string.replace(campo,"(","C")

                if campo.find(")") > 0:
                    campo = string.replace(campo,")","")

                if campo.find("[") > 0:
                    campo = string.replace(campo,"[","")

                if campo.find("]") > 0:
                    campo = string.replace(campo,"]","")

                if campo.find("'") > 0:
                    campo = string.replace(campo,"'","")

                if campo.find("-") > 0:
                    campo = string.replace(campo,"-","")

                if campo.find("_") > 0:
                    campo = string.replace(campo,"_","")

                if campo.find("*") > 0:
                    campo = string.replace(campo,"*","")

                campo = filter(lambda x: not x.isdigit(),campo)

            campo = campo.strip()

            print("CAMPO DEPOIS [%s]" % campo)

            return campo

        except Exception as e:
            print e.message

    def validateDate(self, date_text):

        try:
            datetime.datetime.strptime(date_text,'%d/%m/%Y')
            return True
        except ValueError:
            return False

    def increase_brightness(this,img):
        # convert it to hsv
        hsv = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)

        h,s,v = cv2.split(hsv)
        print v
        print type(v)
        maximo = np.max(v)

        print np.max(h)
        print np.max(s)
        print np.max(v)

        v[v > 10] += 255 - maximo
        # s[s>10] += 254-maximo
        # h[h>10] += 254-maximo

        print v
        final_hsv = cv2.merge((h,s,v))

        img = cv2.cvtColor(final_hsv,cv2.COLOR_HSV2BGR)

        return img

    def hisEqulColor(this,img):
        ycrcb = cv2.cvtColor(img,cv2.COLOR_BGR2YCR_CB)
        channels = cv2.split(ycrcb)
        cv2.equalizeHist(channels[0],channels[0])
        cv2.merge(channels,ycrcb)
        cv2.cvtColor(ycrcb,cv2.COLOR_YCR_CB2BGR,img)
        return img

    def removeRangeColors(self,img):

        lower = np.array([128,136,106])  # -- Lower range --
        upper = np.array([255,255,255])  # -- Upper range --
        mask = cv2.inRange(img,lower,upper)

        return mask

    def removeRangeColors2(self,img):

        r = [img[300,300,0],img[200,500,0],img[500,350,0],img[520,350,0]]
        g = [img[300,300,1],img[200,500,1],img[500,350,1],img[520,350,1]]
        b = [img[300,300,2],img[200,500,2],img[500,350,2],img[520,350,2]]
        # print ("R[%d]G[%d]B[%d]" % r, g, b)

        r = int(min(r))
        g = int(min(g))
        b = int(min(b))
        # print("min R[%d]G[%d]B[%d]" % r, g, b)

        # r = int(np.mean(r))
        # g = int(np.mean(g))
        # b = int(np.mean(b))
        # print("media R[%d]G[%d]B[%d]" % r, g, b)

        #r = self.person_clr_range[0]
        #g = self.person_clr_range[1]
        #b = self.person_clr_range[2]
        #print(self.person_clr_range)

        lower = np.array([r,g,b])
        # lower = np.array([128,136,106])  # -- Lower range --
        upper = np.array([255,255,255])  # -- Upper range --
        mask = cv2.inRange(img,lower,upper)

        return mask

    def order_points(self,pts):
        # initialize a list of coordinates that will be ordered
        # such that the first entry in the list is the top-left,
        # the second entry is the top-right, the third is the
        # bottom-right, and the fourth is the bottom-left
        rect = np.zeros((4,2),dtype="float32")

        # the top-left point will have the smallest sum, whereas
        # the bottom-right point will have the largest sum
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

        # now, compute the difference between the points, the
        # top-right point will have the smallest difference,
        # whereas the bottom-left will have the largest difference
        diff = np.diff(pts,axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]

        # return the ordered coordinates
        return rect

    def sort_contours(cnts,method="left-to-right"):
        # initialize the reverse flag and sort index
        reverse = False
        i = 0

        # handle if we need to sort in reverse
        if method == "right-to-left" or method == "bottom-to-top":
            reverse = True

        # handle if we are sorting against the y-coordinate rather than
        # the x-coordinate of the bounding box
        if method == "top-to-bottom" or method == "bottom-to-top":
            i = 1

        # construct the list of bounding boxes and sort them from top to
        # bottom
        boundingBoxes = [cv2.boundingRect(c) for c in cnts]
        (cnts,boundingBoxes) = zip(*sorted(zip(cnts,boundingBoxes),
                                           key=lambda b: b[1][i],reverse=reverse))
        # return the list of sorted contours and bounding boxes
        return (cnts,boundingBoxes)

    def processa_campo(self,campo,y,idx,h):

        cv2.imwrite('/tmp/campo_%d.png' % idx,campo)

        img = Image.open('/tmp/campo_%d.png' % idx)

        ##convert from Image to array
        arr_doc = np.asarray(img)

        arr_doc = cv2.cvtColor(arr_doc,cv2.COLOR_BGR2GRAY)

        cv2.imwrite('/tmp/campo_%d.png' % idx,arr_doc)

        # convert from array to Image
        img = Image.fromarray(np.uint8(img))

        # OCR
        texto_d = pytesseract.image_to_string(img,config='-psm 7 digits -l por')
        texto_c = pytesseract.image_to_string(img,config='-psm 7 -l por')
        print "Campo ---> idx: %d y: %d h: %d [%s][%s:%d] " % (idx,y,h,texto_d,texto_c,len(texto_c))
        return [texto_c]

    def encontra_doc(t,rg):
        contours,hierarchy = cv2.findContours(t,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        display = np.array(rg,copy=True)

        print "Foram encontrados %d contornos grandes" % (len(contours))

        # cnts = sorted(contours, key=cv2.contourArea,reverse=True)[:5]
        cnts = sorted(contours,key=cv2.contourArea)


        for idx,cnt in enumerate(cnts):
            x,y,w,h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)

            if (h >= 450 and h <= 700) and w > 700:  # muito ruim esse 55 manual
                cv2.rectangle(display,(x,y),(x + w,y + h),(0,0,255),4)

                return [t[y:y + h,x:x + w],rg[y:y + h,x:x + w]]

                # cv2.rectangle(display,(x,y),(x+w,y+h),(255,0,0),2)

                # processa_campo (thresh[y:y+h,x:x+w])

    def doc_recognition(self):

        rg = None

        if self.doc_side == "VERSO":

            rg = cv2.resize(self.doc_img,(800,600))
            #cv2.imwrite(img_path + "ori.jpg",rg)

            print rg.shape

            mask = self.removeRangeColors(rg)
            cv2.imwrite(img_path + "mask.jpg", mask)

            #aux = self.hisEqulColor(rg)

            # teste threshold personalizado
            #========================================================================
            aux = cv2.cvtColor(rg,cv2.COLOR_BGR2GRAY)

            mask_mean_c = cv2.adaptiveThreshold(aux,255,cv2.ADAPTIVE_THRESH_MEAN_C,
                                                cv2.THRESH_BINARY,3,2)
            cv2.imwrite(img_path + "mask_mean_c.jpg",mask_mean_c)

            mask_gaussian_c = cv2.adaptiveThreshold(aux,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                    cv2.THRESH_BINARY,3,2)
            cv2.imwrite(img_path + "mask_gaussian_c.jpg",mask_gaussian_c)

            ## remove noise
            kernel = np.ones((2,2),np.uint8)
            closing = cv2.morphologyEx(mask_gaussian_c,cv2.MORPH_CLOSE,kernel)
            cv2.imwrite(img_path + "closing.jpg", closing)
            # ========================================================================

            #blur = cv2.blur(closing,(2,2))
            #cv2.imwrite(img_path + "blur.jpg",blur)

            ## remove noise
            #kernel = np.ones((5,2),np.uint8)
            #opening = cv2.morphologyEx(closing,cv2.MORPH_OPEN,kernel)
            #cv2.imwrite(img_path + "opening.jpg", opening)

            ## increases the white region of the image
            #kernel = np.ones((1,1),np.uint8)
            #dilate = cv2.dilate(opening,kernel,iterations=5)
            #cv2.imwrite(img_path + "dilate.jpg", dilate)

            ##aplica o embaçador
            # blur = cv2.blur(dilate,(1,1))
            # ========================================================================

            ## fecha os espacos das bordas superior e inferior
            mask_fc = np.array(closing,copy=True)
            #mask_fc = np.array(mask,copy=True)
            horizontalSize = 6
            verticalSize = 17
            horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT,(horizontalSize,verticalSize))
            mask_fc = cv2.morphologyEx(mask_fc,cv2.MORPH_OPEN,horizontalStructure)

            if self.doc_version == PERTO_BORDA:
                horizontalSize = 5
                verticalSize = 3
                horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT,(horizontalSize,verticalSize))
                mask_fc = cv2.morphologyEx(mask_fc,cv2.MORPH_OPEN,horizontalStructure)

            elif self.doc_version == LONGE_BORDA:
                horizontalSize = 7
                verticalSize = 1
                horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT,(horizontalSize,verticalSize))
                mask_fc = cv2.morphologyEx(mask_fc,cv2.MORPH_OPEN,horizontalStructure)

            cv2.imwrite(img_path + "mask_fc.jpg",mask_fc)

            ## encontra os pontos da borda interior
            _,contours,hierarchy = cv2.findContours(mask_fc,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
            display_doc = np.array(rg,copy=True)

            print "Foram encontrados %d contornos grandes" % (len(contours))

            ## ordeno os contornos em ordem reversa (menor -> maior) e pego soh o primeiro (menor)
            contours = sorted(contours,key=cv2.contourArea,reverse=True)[:1]

            sorted(contours,key=cv2.contourArea,reverse=True)
            for idx,cnt in enumerate(contours):
                x,y,w,h = cv2.boundingRect(cnt)
                doc = None

                if h >= 250 and w > 300:  # muito ruim esse 55 manual

                    peri = cv2.arcLength(cnt,True)
                    approx = cv2.approxPolyDP(cnt,0.02 * peri,True)

                    # if our approximated contour has four points, then we
                    # can assume that we have found our screen
                    print "approx: %d " % (len(approx))

                    if len(approx) >= 4 and len(approx) <= 12:
                        screenCnt = approx
                        cv2.drawContours(display_doc,[screenCnt],-1,(255,0,0),5)

                        cv2.imwrite(img_path + "contornos.jpg",display_doc)

                        # joga os pontos em uma lista para ordenacao
                        myList = []
                        for p in approx:
                            xc,yc = p[0]
                            myList.append([xc,yc])

                        pts = np.array(myList,dtype="float32")
                        print(pts)

                        # desenha os circulos no local onde encontrou os pontos
                        ordered_points = self.order_points(pts)

                        for p in ordered_points:
                            xc,yc = p
                            cv2.circle(display_doc,(xc,yc),10,(0,255,0),3)

                        area1 = cv2.contourArea(ordered_points)
                        area2 = cv2.contourArea(cnt)

                        print ("Area1: %d Area2: %d (len %d)" % (area1,area2,len(ordered_points)))
                        print ordered_points

                        #
                        # recorta o DOC e corrige o warpPerspective
                        #

                        # pontos originais
                        quad_pts = ordered_points

                        # pontos na nova imagem 700 x 525
                        myList = [[0,0],[0,0 + 525],[0 + 700,0],[0 + 700,0 + 525]]
                        squre_pts = self.order_points(np.array(myList,dtype="float32"))

                        transmtx = cv2.getPerspectiveTransform(quad_pts,squre_pts)

                        transformed = cv2.warpPerspective(rg,transmtx,(700,525))
                        # transformed = cv2.resize(transformed,(700,525))

                        # vamos passar a usar DOC ao inves de RG
                        # doc e o miolo recortado e com perspectiva corrigida
                        doc = transformed

                        #cv2.imwrite(img_path + "doc_2.jpg",doc)

                        cv2.rectangle(display_doc,(x,y),(x + w,y + h),(0,0,255),4)
                        # cv2.imwrite(img_path + "display_doc.jpg",display_doc)

                cv2.imwrite(img_path + "display_doc.jpg",display_doc)

                if doc is None:
                    print("Error:: Didn't find corners")
                    return 0


                if (self.doc_version == PERTO_BORDA):
                    arr_doc = cv2.cvtColor(doc,cv2.COLOR_BGR2GRAY)

                    ##It makes the reduction of a graylevel image to a binary image (Also uses THRESH_OTSU) THRESH_BINARY
                    # (retval,thresh) = cv2.threshold(arr_doc,150,255,cv2.THRESH_BINARY)
                    (retval,mask) = cv2.threshold(arr_doc,130,255,cv2.THRESH_BINARY)


                elif (self.doc_version == LONGE_BORDA):
                    mask = self.removeRangeColors(doc)


                #cv2.imwrite(img_path + "doc.jpg",doc)
                #cv2.imwrite(img_path + "mask_2.jpg",mask)

                horizontalSize = 2
                verticalSize = 1
                horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT,(horizontalSize,verticalSize))
                # horizontalStructure [:,0:2] = 0
                # horizontalStructure [:,4:6] = 0
                #print horizontalStructure
                blocos = cv2.erode(mask,horizontalStructure,(-1,-1),iterations=18)

                cv2.imwrite(img_path + "blocos.jpg",blocos)

                # encontra os retangulos dos nomes
                _,contours,hierarchy = cv2.findContours(blocos,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

                display = np.array(doc,copy=True)

                # processa os retangulos com os campos encontrados
                #
                # Estamos usando a variavel "doc" como o documento a ser recortado e enviado para o OCR
                #
                campos = {}
                frames = {}
                linha = 0
                for idx,cnt in enumerate(contours):
                    x,y,w,h = cv2.boundingRect(cnt)
                    area = cv2.contourArea(cnt)

                    if area >= 300 and h > 18 and h < 80:
                        if x > 2:
                            x = x - 2
                        if y > 2:
                            y = y - 2
                        h = h + 4
                        w = w + 4

                        cv2.rectangle(display,(x,y),(x + w,y + h),(0,0,255),3)
                        self.processa_campo(doc[y:y + h,x:x + w],y,idx,h)

                        linha = (y / 35) + 1

                        # se o campo for muito alto, provavelmente leu a descricao do campo que fica acima do valor
                        # reduzo o tamanho do campo e somo a diferenca no y
                        if h > 39:
                            dif = h - 39
                            y = y + dif
                            h = h - dif

                        # processa_campo (ori[y:y+h,x:x+w],y,idx,h)
                        # print y,last,cy
                        if linha in campos.keys():
                            arr = campos[linha]
                            arr[x] = (doc[y - 2:y + h + 2,x - 2:x + w + 2])
                            campos[linha] = arr

                            farr = frames[linha]
                            farr[x] = (x,y,w,h)
                            frames[linha] = farr

                        else:
                            arr = {}
                            arr[x] = (doc[y:y + h,x:x + w])
                            campos[linha] = arr

                            farr = {}
                            farr[x] = (x,y,w,h)
                            frames[linha] = farr

                # le cada campo por linha e vai concatenando seus valores para formar a string final e popula a classe RG
                # lembrando que um nome por exemplo, tem sido encontrado por palavras, e nao pelo nome inteiro
                # por isso entao essa concatenacao
                texto = "-------->"
                rg = RG()

                # doc_type = LONGE_BORDA

                for linha in sorted(campos):

                    for x in sorted(campos[linha]):

                        # manda para o ocr
                        ocr = self.processa_campo(campos[linha][x],linha,0,0)

                        texto = "(x: %d linha: %d) %s %s" % (x,linha,texto,ocr[0])

                        if self.doc_version == LONGE_BORDA:
                            if linha == 1 and x < 300:
                                aux = ocr[0].replace(' ','')
                                rg.numero = self.trata_campo(aux,"RG")
                                rg.numero_lnh = linha

                            if linha == 2 and rg.numero == "" and x < 300:
                                aux = ocr[0].replace(' ','')
                                rg.numero = self.trata_campo(aux,"RG")
                                rg.numero_lnh = linha

                            if linha == 1 and x > 300:
                                aux = ocr[0].replace(' ','')
                                rg.dt_emissao = self.trata_campo(aux,"DATA")
                                rg.dt_emissao_lnh = linha

                            if linha == 2 and rg.dt_emissao == "" and x > 300:
                                aux = ocr[0].replace(' ','')
                                rg.dt_emissao = self.trata_campo(aux,"DATA")
                                rg.dt_emissao_lnh = linha

                            if linha >= 2 and linha <= 3:
                                aux = rg.nome + " " + ocr[0].replace(' ','')
                                rg.nome = self.trata_campo(aux,"NOME")
                                rg.nome_lnh = linha

                            if linha >= 4 and linha <= 5:
                                aux = rg.nome_pai + " " + ocr[0].replace(' ','')
                                rg.nome_pai = self.trata_campo(aux,"NOME")
                                rg.nome_pai_lnh = linha

                            if linha >= 6 and linha <= 7:
                                aux = rg.nome_mae + " " + ocr[0].replace(' ','')
                                rg.nome_mae = self.trata_campo(aux,"NOME")

                            if linha == 8 and x > 400:
                                aux = ocr[0]
                                rg.dt_nascto = self.trata_campo(aux,"DATA")
                                rg.dt_nascto_lnh = linha

                            if linha >= 8 and linha <= 9 and x < 300:
                                aux = rg.naturalidade + " " + ocr[0]
                                rg.naturalidade = self.trata_campo(aux,"NAT")
                                rg.naturalidade_lnh = linha


                        elif self.doc_version == PERTO_BORDA:
                            if linha >= 1 and linha <= 2 and x < 200:
                                aux = ocr[0]
                                rg.numero = self.trata_campo(aux,"RG")
                                rg.numero_lnh = linha

                            if linha >= 1 and linha <= 2 and x > 300:
                                aux = ocr[0]
                                rg.dt_emissao = self.trata_campo(aux,"DATA")
                                rg.dt_emissao_lnh = linha

                            if linha >= 3 and linha <= 4:
                                aux = ocr[0]
                                rg.nome = self.trata_campo(aux,"NOME")
                                rg.nome_lnh = linha

                            ## trata possiveis variações de posição do nome dos pais
                            # =======================================
                            if linha == 5:
                                aux = ocr[0]
                                rg.nome_pai = self.trata_campo(aux,"NOME")
                                rg.nome_pai_lnh = linha

                            if linha == 6 and rg.nome_pai != "":
                                aux = ocr[0]
                                rg.nome_mae = self.trata_campo(aux,"NOME")
                                rg.nome_mae_lnh = linha

                            if linha == 6 and rg.nome_pai == "":
                                aux = ocr[0]
                                rg.nome_pai = self.trata_campo(aux,"NOME")
                                rg.nome_pai_lnh = linha

                            if linha == 7 and rg.nome_pai != "" and rg.nome_mae == "":
                                aux = ocr[0]
                                rg.nome_mae = self.trata_campo(aux,"NOME")
                                rg.nome_mae_lnh = linha

                            if linha == 7 and rg.nome_pai == "":
                                aux = ocr[0]
                                rg.nome_pai = self.trata_campo(aux,"NOME")
                                rg.nome_pai_lnh = linha

                            if linha == 7 and rg.nome_pai != "" and rg.nome_mae == "":
                                rg.nome_mae = rg.nome_pai
                                rg.nome_mae_lnh = rg.nome_pai_lnh
                                rg.nome_pai = ""
                                rg.nome_pai_lnh = 0

                            ## trata possiveis variações de posição na dt_nasc
                            # =======================================
                            if linha == 8 and x > 400:
                                aux = ocr[0]
                                rg.dt_nascto = self.trata_campo(aux,"DATA")
                                rg.dt_nascto_lnh = linha

                            if linha == 9 and x > 400 and rg.dt_nascto == "":
                                aux = ocr[0]
                                rg.dt_nascto = self.trata_campo(aux,"DATA")
                                rg.dt_nascto_lnh = linha

                            ## trata possiveis variações de posição no campo naturalidade
                            # =======================================
                            if linha == 8 and x < 150:
                                aux = ocr[0]
                                rg.naturalidade = self.trata_campo(aux,"NAT")
                                rg.naturalidade_lnh = linha

                            if linha == 9 and x < 150 and rg.naturalidade == "":
                                aux = ocr[0]
                                rg.naturalidade = self.trata_campo(aux,"NAT")
                                rg.naturalidade_lnh = linha

                    print texto
                    texto = "-------->"

                # tenta encontrar problemas e usar algumas inferencias para resolve-los
                if self.doc_version == LONGE_BORDA:

                    linha = 1
                    if rg.numero == "" or len(rg.numero) < 10:
                        print "campo -- numero -- nao encontrado ou com possivel erro"
                        for linha in sorted(campos):
                            if linha == rg.dt_emissao_lnh:
                                break
                        x = sorted(frames[linha])[0]
                        (x,y,w,h) = frames[linha][x]

                        x = x - 5
                        w = 250
                        y = y
                        h = h + 3
                        cv2.rectangle(display,(x,y),(x + w,y + h),(20,20,20),3)
                        ocr = self.processa_campo(doc[y:y + h,x:x + w],linha,0,0)
                        rg.numero = ocr[0]

                    if rg.dt_emissao == "":
                        print "campo -- dt.emissao -- nao encontrado"
                        for linha in sorted(campos):
                            if linha == rg.numero_lnh:
                                break

                        x = sorted(frames[linha])[0]
                        (x,y,w,h) = frames[linha][x]

                        x = x + 360
                        w = 218
                        y = y - 6
                        h = 38
                        cv2.rectangle(display,(x,y),(x + w,y + h),(20,20,20),3)
                        ocr = self.processa_campo(doc[y:y + h,x:x + w],linha,0,0)
                        aux = ocr[0]
                        rg.dt_emissao = self.trata_campo(aux,"DATA")

                    ## 	if len(rg.emissao) < 9:
                    ## 		w = 230
                    ## 		cv2.rectangle(display,(x,y),(x+w,y+h),(20,20,20),3)
                    ## 		ocr = processa_campLo (ori[y:y+h,x:x+w],linha,0,0)
                    ## 		rg.emissao = ocr[0]

                    if rg.dt_nascto == "":
                        print "campo -- dt.dt_nascto -- nao encontrado"
                        linha = 1
                        for linha in sorted(campos):
                            if linha == rg.naturalidade_lnh:
                                break

                        x = sorted(frames[linha])[0]
                        (x,y,w,h) = frames[linha][x]

                        x = x + 438
                        w = 233
                        y = y - 7
                        h = 38
                        cv2.rectangle(display,(x,y),(x + w,y + h),(20,20,20),3)
                        ocr = self.processa_campo(doc[y:y + h,x:x + w],linha,0,0)
                        aux = ocr[0].strip()
                        rg.dt_nascto = self.trata_campo(aux,"DATA")

                        ## 	if len(rg.dt_nascto.decode('utf-8')) < 11:
                        ## 		w = 280
                        ## 		cv2.rectangle(display,(x,y),(x+w,y+h),(20,20,20),2)
                        ## 		ocr = processa_campo (ori[y:y+h,x:x+w],linha,0,0)
                        ## 		rg.dt_nascto = ocr[0]
                        #     print "\n\n============== Dados do RG ====================="

                if self.doc_version == PERTO_BORDA:
                    if rg.naturalidade == "":
                        print "campo -- naturalidade -- nao encontrado"
                        linha = 1
                        for linha in sorted(campos):
                            if linha == rg.dt_nascto_lnh:
                                break

                        x = sorted(frames[linha])[0]
                        (x,y,w,h) = frames[linha][x]

                        x = x - 500
                        w = 300
                        y = y - 7
                        h = 34
                        cv2.rectangle(display,(x,y),(x + w,y + h),(20,20,20),3)
                        ocr = self.processa_campo(doc[y:y + h,x:x + w],linha,0,0)
                        aux = ocr[0].strip()
                        rg.naturalidade = self.trata_campo(aux,"NAT")

                print ("")
                print ("==========================================================")
                print ("NUMERO       [%s]" % rg.numero)
                print ("EMISSAO      [%s]" % rg.dt_emissao)
                print ("NOME         [%s]" % rg.nome)
                print ("PAI          [%s]" % rg.nome_pai)
                print ("MAE          [%s]" % rg.nome_mae)
                print ("DT_NASC      [%s]" % rg.dt_nascto)
                print ("NATURALIDADE [%s]" % rg.naturalidade)
                #print ("CPF [%s]" % rg.cpf)

                cv2.imwrite(img_path + "display.jpg",display)

            return rg


if __name__ == "__main__":

    # rg = cv2.imread ('/home/tercio/projects/projects_cm/CM/DocReader/Imagens/rg_bia.jpg',1)
    # rg = cv2.imread ('/home/tercio/projects/projects_cm/CM/DocReader/Imagens/rg_tercio.jpg',1)
    # rg = cv2.imread ('/home/tercio/projects/projects_cm/CM/DocReader/Imagens/rg_tercio_2.jpg',1)
    # rg = cv2.imread ('/home/tercio/projects/projects_cm/CM/DocReader/Imagens/rg_daiane.jpg',1)
    # rg = cv2.imread ('/home/tercio/projects/projects_cm/CM/DocReader/Imagens/rg_daiane_2.jpg',1)

    # rg = cv2.imread ('/home/tercio/projects/projects_cm/CM/DocReader/Imagens/rg_tercio_app.jpg',1)
    # rg = cv2.imread ('/home/tercio/projects/projects_cm/CM/DocReader/Imagens/rg_flavia_app.jpg',1)
    # rg = cv2.imread ('/home/tercio/projects/projects_cm/CM/DocReader/Imagens/rg_heitor_app.jpg',1)
    # rg = cv2.imread ('/home/tercio/projects/projects_cm/CM/DocReader/Imagens/rg_daniela_app.jpg',1)
    # rg = cv2.imread ('/home/tercio/projects/projects_cm/CM/DocReader/Imagens/rg_erica_app.jpg',1)
    # rg = cv2.imread ('/home/tercio/projects/projects_cm/CM/DocReader/Imagens/rg_daiane_3_app.jpg',1)
    # rg = cv2.imread ('/home/tercio/projects/projects_cm/CM/DocReader/Imagens/rg_juliana_app.jpg',1)

    files = ['rg_daiane_3_app.jpg']

    '''files = ['rg_flavia_app.jpg',
             'rg_heitor_app.jpg',
             'rg_erica_app.jpg',
             'rg_daiane_3_app.jpg',
             
             'rg_daniela_app.jpg',
             'rg_juliana_app.jpg'
             ]'''

    for f in files:
        rg = cv2.imread(img_path + f, 1)

        doc_reader = RgReader(LONGE_BORDA,"VERSO",rg)
        doc_reader.doc_recognition()
