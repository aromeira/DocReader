import cv2
import numpy as np
import pytesseract

try:
    import Image
except ImportError:
    from PIL import Image
from itertools import groupby

from CNH import CNH

path_aux = "/home/danielle/projects/python/pyParseDocts/"

class CnhReader:
    def __init__(self,lado_doc,img):
        self.lado_doc = lado_doc
        self.img = img

    def order_points(self,pts):
        # initialzie a list of coordinates that will be ordered
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

    def remove_doc(self,img,top_left_colsAndRows,top_right_colsAndRows):

        # print top_left_colsAndRows
        # print
        # print top_right_colsAndRows

        quad_pts = []

        x = top_left_colsAndRows[0][0]
        if x - 10 > 0:
            x = x - 10
        else:
            x = 0

        y = top_left_colsAndRows[0][1]
        if y > 10:
            y = y - 10
        else:
            y = 0

        yh = top_left_colsAndRows[-1][1]

        # tentar buscar o valor mais a esquerda para o ultimo Y (meio porco)
        for xt,yt in reversed(top_left_colsAndRows):
            if yh != yt:
                break
            xh = xt

        if xh > 200:
            xh = x

        if yh + 60 < img.shape[0]:
            yh = yh + 60
        else:
            yh = img.shape[0]

        xw = top_right_colsAndRows[0][0]
        if xw + 10 < img.shape[1]:
            xw = xw + 10
        else:
            xw = img.shape[1]

        if xh - 10 > 0:
            xh = xh - 10
        else:
            xh = 0

        xwh = top_right_colsAndRows[-1][0]
        if xwh + 10 < img.shape[1]:
            xwh = xwh + 10
        else:
            xwh = img.shape[1]

        if xwh < xw * 0.8:  # provavelmente um ponto errado foi encontrado
            xwh = xw

        yw = top_right_colsAndRows[0][1]
        if yw - 17 > 0:
            yw = yw - 17
        else:
            yw = 0

        if yw > y + 40:  # provavelmente nao foi encontrado o yw (corner nao encontrado?)
            yw = y

        yhw = top_right_colsAndRows[-1][1]
        if yhw + 60 < img.shape[0]:
            yhw = yhw + 60  # 58
        else:
            yhw = img.shape[0]

        # print ("x %d  y %d  xw %d  xh %d  xwh %d  yh %d  yhw %d  yw %d" % (x,y,xw,xh,xwh,yh,yhw,yw))
        display_doc = np.array(img,copy=True)
        cv2.circle(display_doc,(x,y),10,(0,255,0),3)
        cv2.circle(display_doc,(xw,yw),10,(0,255,255),3)
        cv2.circle(display_doc,(xh,yh),10,(0,0,255),3)
        cv2.circle(display_doc,(xwh,yhw),10,(255,0,0),3)
        # cv2.imshow ('circles',display_doc)


        # x,y
        quad_pts.append([x,y])
        # x+w,y
        quad_pts.append([xw,yw])
        # xh,y+h
        quad_pts.append([xh,yh])
        # x+wh,yw+h
        quad_pts.append([xwh,yhw])

        # pontos na nova imagem 700 x 525
        myList = [[0,0],[0,0 + 550],[0 + 734,0],[0 + 734,0 + 550]]
        squre_pts = self.order_points(np.array(myList,dtype="float32"))

        t = np.array(quad_pts,dtype=np.float32)
        # print t
        # print squre_pts
        ordered_points = self.order_points(t)
        transmtx = cv2.getPerspectiveTransform(ordered_points,squre_pts)

        transformed = cv2.warpPerspective(img,transmtx,(734,550))
        transformed = cv2.resize(transformed,(734,550))

        # vamos passar a usar DOC ao inves de RG
        # doc e o miolo recortado e com perspectiva corrigida
        doc = transformed

        # cv2.imshow('doc',doc)
        # cv2.waitKey(0)

        return doc

    def order_corners(self,corners):

        linha = corners[0][1]
        out = []

        # ordena por linha
        for tup in sorted(corners,key=lambda tup: tup[1]):  # ordena por linha e entao equipara as pequenas diferencas

            if tup[1] - linha > 8:
                linha = tup[1]

            out.append((tup[0],linha))

        # agrupa por linha
        groups = groupby(out,key=lambda tup: tup[1])

        # ordena por colunas dentro de cada grupo de linhas
        out = []
        for linha,group in groups:
            out.extend(sorted(group,key=lambda tup: tup[0]))

        # print out
        return out

    def find_corner(self,img,pos='top_right',doc=False):
        # small_image = cv2.imread('/home/tercio/projects/projects_cm/CM/DocReader/borda.jpg')
        # small_image = cv2.imread('/home/tercio/projects/projects_cm/CM/DocReader/top_left.jpg')
        #small_image = cv2.imread('/home/tercio/projects/projects_cm/CM/DocReader/%s.jpg' % (pos))
        small_image = cv2.imread(path_aux + '%s.jpg' % (pos))

        ## NOTA ! ! ! ! Aparentemente, o segredo para um bom patch, esta em recortar bem rente a linha esquerda para
        #               conseguir pegar ainda os que enconstam no canto e tambem recortar abaixo da curva pegando um
        #               pouco mais para fora do campo e tambem uma area maior dentro da propria linha do campo
        #               para que nao se confunda com letras O 0, C etc

        method = cv2.TM_CCOEFF_NORMED

        large_image = img

        display = np.array(img,copy=True)

        # print large_image.dtype
        # print small_image.dtype

        result = cv2.matchTemplate(small_image,large_image,method)
        # print result

        # We want the minimum squared difference
        # mn,_,mnLoc,_ = cv2.minMaxLoc(result)

        h,w = small_image.shape[:-1]
        threshold = .8

        import random
        rcolor = lambda: (random.randint(0,255),random.randint(0,255),random.randint(0,255))
        randomColor = rcolor()

        loc = np.where(result >= threshold)

        colsAndRows = []
        for pt in zip(*loc[::-1]):  # Switch collumns and rows

            if pt[0] > img.shape[1] / 3 and pt[1] < 80 and pos == 'top_left' and doc == False:
                continue

            cv2.rectangle(display,pt,(pt[0] + w,pt[1] + h),randomColor,2)
            colsAndRows.append(pt)

        # Display the original image with the rectangle around the match.
        # cv2.imshow('output',display)
        # cv2.waitKey(0)

        # The image is only displayed if we call this

        return [display,colsAndRows]

    def sort_contours(self,cnts,method="left-to-right"):
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

    def remove_linha_inferior(self,campo):
        last = np.sum(campo[campo.shape[0] - 15,:])
        for y in range(campo.shape[0] - 15,campo.shape[0]):
            # print ("%d %d" % (np.sum(campo[y,:]),last * 0.15) )
            campo2 = campo[0:y,:]
            ##cv2.imshow ('removelinhainferior',campo2)
            # cv2.waitKey(0)
            if np.sum(campo[y,:]) > last * 1.2:
                break;
            last = np.sum(campo[y,:])

        campo = campo[0:y,:]

        return campo

    def encontra_campos(self,img,top_left_colsAndRows,top_right_colsAndRows):

        cnh = CNH()

        display = np.array(img,copy=True)

        l1,h1 = top_left_colsAndRows[0]
        r1,h2 = top_right_colsAndRows[0]

        if h2 > h1 + 40:
            h2 = h1

            # print l1,h1
        # print r1,h2

        #
        # procura o campo nome para iniciar o processo
        #
        linha_atual = 0
        largura_nome = 0
        if (r1 - l1) > (img.shape[1] / 2) and abs(
                        h1 - h2) <= 15:  # se a largura do primeiro campo encontrado e maior que a metade da imagem, devemos ter o campo nome

            linha_atual = h1
            largura_nome = r1

            cv2.rectangle(display,(l1 + 5,h1),(r1,h2 + 50),(0,0,255),2)

            campo = img[h1 + 10:h2 + 50,l1 + 5:r1]
            campo_ori = np.array(campo,copy=True)

            display_cnt = np.array(campo,copy=True)

            campo = cv2.cvtColor(campo,cv2.COLOR_BGR2GRAY)

            # cv2.imshow('btiwise',campo)
            # cv2.waitKey(0)

            ret,campo = cv2.threshold(campo,160,255,cv2.THRESH_BINARY_INV)
            # cv2.imshow('thresh',campo)


            horizontalSize = 6
            verticalSize = 1
            horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT,(horizontalSize,verticalSize))
            horizontalStructure[:,0:2] = 0
            # horizontalStructure [:,4:6] = 0
            # print horizontalStructure
            campo = cv2.dilate(campo,horizontalStructure,(-1,-1),iterations=3)
            # cv2.imshow('campo nome',campo)


            _,contours,hierarchy = cv2.findContours(campo,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
            # print "Foram encontrados %d contornos" % (len(contours))
            (sorted_contours,boundingBoxes) = self.sort_contours(contours)

            nome = ""

            for idx,cnt in enumerate(sorted_contours):
                x,y,w,h = cv2.boundingRect(cnt)

                area = cv2.contourArea(cnt)

                if area >= 180 and w < 200 and h > 12:
                    cv2.rectangle(display_cnt,(x + 2,y - 1),(x + w - 2,y + h + 1),(10,10,10),1)
                    palavra = campo_ori[y - 1:y + h + 1,x + 2:x + w - 2]
                    ocr = self.processa_campo(palavra,-1,0,0)
                    nome = nome + " " + ocr[1].replace(' ','')
                    # cv2.imshow('palavra',palavra)

            # cv2.imshow('palavras',display_cnt)

            # print ("Nome: %s" % (nome))
            cnh.nome = nome.strip()

            # cv2.waitKey(0)

            #
            # rg
            #

            # cv2.destroyAllWindows()

            for x,y in top_left_colsAndRows:
                if y > linha_atual + 40:
                    break

            # print y
            linha_atual = y

            l1 = x
            h1 = y

            #
            # temos que encontrar o ponto direito aproximado em relacao ao esquerdo
            #
            for x,y in top_right_colsAndRows:
                if y >= (linha_atual - 5) and y <= (linha_atual + 5):
                    break

            # print ("linha atual: %d -> right y: %d" % (linha_atual,y))
            r1 = x

            # caso nao encontre o marcador da direita
            if y >= (linha_atual - 5) and y <= (linha_atual + 5):
                h2 = y
            else:
                h2 = linha_atual

            display = np.array(img,copy=True)

            cv2.rectangle(display,(l1 + 5,h1),(r1,h2 + 50),(0,0,255),2)

            campo = img[h1 + 10:h2 + 50,l1 + 5:r1]
            campo_ori = np.array(campo,copy=True)

            display_cnt = np.array(campo,copy=True)

            campo = cv2.cvtColor(campo,cv2.COLOR_BGR2GRAY)

            # cv2.imshow('btiwise',campo)
            # cv2.waitKey(0)

            ret,campo = cv2.threshold(campo,160,255,cv2.THRESH_BINARY_INV)
            # cv2.imshow('thresh',campo)


            horizontalSize = 5
            verticalSize = 1
            horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT,(horizontalSize,verticalSize))
            # horizontalStructure [:,0:2] = 0
            # horizontalStructure [:,4:6] = 0
            # print horizontalStructure
            campo = cv2.dilate(campo,horizontalStructure,(-1,-1),iterations=2)
            # cv2.imshow('campo nome',campo)



            _,contours,hierarchy = cv2.findContours(campo,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
            # print "Foram encontrados %d contornos" % (len(contours))
            (sorted_contours,boundingBoxes) = self.sort_contours(contours)

            rg = ""

            for idx,cnt in enumerate(sorted_contours):
                x,y,w,h = cv2.boundingRect(cnt)

                area = cv2.contourArea(cnt)

                # print ("%d %d %d %d (%d, %d)" % (x,y,w,h,campo_ori.shape[0],area))
                if area >= 800 and w < 400 and h > 12:
                    cv2.rectangle(display_cnt,(x + 2,y - 1),(x + w - 2,y + h + 1),(10,10,10),1)
                    palavra = campo_ori[y - 1:y + h + 1,x + 2:x + w - 2]
                    ocr = self.processa_campo(palavra,-1,0,0)
                    rg = rg + " " + ocr[1].replace(' ','')
                    # cv2.imshow('palavra',palavra)

            # cv2.imshow('palavras',display_cnt)

            # print ("rg: %s" % (rg))
            cnh.rg = rg.strip()

            # cv2.waitKey(0)


            #
            # cpf e dt_nascto
            #

            # cv2.destroyAllWindows()

            for x,y in top_left_colsAndRows:
                if y > linha_atual + 40:
                    break

            # print y
            linha_atual = y

            l1 = x
            h1 = y

            #
            # temos que encontrar o ponto direito aproximado em relacao ao esquerdo
            #
            # print x
            # print y
            # print top_right_colsAndRows
            for x,y in reversed(top_right_colsAndRows):
                if y >= (linha_atual - 5) and y <= (linha_atual + 5):
                    break

            # print ("linha atual: %d -> right y: %d" % (linha_atual,y))
            r1 = x

            # caso nao encontre o marcador da direita
            if y >= (linha_atual - 5) and y <= (linha_atual + 5):
                h2 = y
            else:
                h2 = linha_atual

            display = np.array(img,copy=True)

            cv2.rectangle(display,(l1 + 5,h1),(r1,h2 + 50),(0,0,255),2)

            campo = img[h1 + 10:h2 + 50,l1 + 5:r1]
            campo_ori = np.array(campo,copy=True)

            display_cnt = np.array(campo,copy=True)

            campo = cv2.cvtColor(campo,cv2.COLOR_BGR2GRAY)

            # cv2.imshow('btiwise',campo)

            ret,campo = cv2.threshold(campo,120,255,cv2.THRESH_BINARY_INV)

            horizontalSize = 5
            verticalSize = 1
            horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT,(horizontalSize,verticalSize))
            # horizontalStructure [:,0:2] = 0
            # horizontalStructure [:,4:6] = 0
            # print horizontalStructure
            # campo = cv2.dilate (campo,horizontalStructure,(-1,-1),iterations=2)
            # cv2.imshow('campo nome',campo)
            # cv2.waitKey(0)


            _,contours,hierarchy = cv2.findContours(campo,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
            # print "Foram encontrados %d contornos" % (len(contours))
            (sorted_contours,boundingBoxes) = self.sort_contours(contours)

            cpf = ""
            dt_nascto = ""
            field = 1
            xini = 0
            yini = 0
            xend = 0
            lastx = 0
            lasty = 0
            for idx,cnt in enumerate(sorted_contours):
                x,y,w,h = cv2.boundingRect(cnt)

                area = cv2.contourArea(cnt)

                # print ("%d %d %d %d (%d, %d)" % (x,y,w,h,campo_ori.shape[0],area))
                if h >= 11 and h < campo_ori.shape[0] - 6 and area < 230:
                    if xini == 0:
                        xini = x
                        yini = y
                    lastx = x
                    lasty = y
                    lastw = w
                    lasth = h

                    cv2.rectangle(display_cnt,(x - 2,y - 1),(x + w + 2,y + h + 2),(10,10,10),1)
                    # palavra = campo_ori[y-1:y+h+2,x-2:x+w+2]
                    # ocr = processa_campo (palavra,-1,0,0)
                    # print ("ocr: %s (%d %d %d %d)" % (ocr[1],x,y,w,h))
                    # cpf = cpf + " " + ocr[1].replace(' ','')
                    ##cv2.imshow('palavra',palavra)
                    # cv2.imshow('display_cnt',display_cnt)
                    # cv2.waitKey(0)

                elif h > campo_ori.shape[0] - 6 and area < 190:  # marcador ?
                    if field == 2:
                        continue
                        # print "marcador --- "
                    field = 2
                    xend = lastx
                    # cv2.rectangle(display_cnt,(xini-2,yini-2),(xend+lastw+4,yini+lasth+2),(0,0,255),2)
                    # cv2.imshow('display_cnt',display_cnt)
                    # cv2.waitKey(0)

                    palavra = campo_ori[yini - 2:yini + lasth + 4,xini - 2:xend + lastw + 2]

                    ocr = self.processa_campo(palavra,-1,0,0)
                    # print ("ocr: %s (%d %d %d %d)" % (ocr[1],x,y,w,h))
                    # cv2.imshow('palavra',palavra)
                    cpf = cpf + " " + ocr[1].replace(' ','')

                    xini = 0
                    yini = 0
                    xend = 0
                    lastx = 0
                    lasty = 0
                    # cv2.waitKey(0)

            if field == 2:
                xend = lastx
                cv2.rectangle(display_cnt,(xini - 2,yini - 2),(xend + lastw + 4,yini + lasth + 2),(0,0,255),2)

                palavra = campo_ori[yini - 2:yini + lasth + 4,xini - 2:xend + lastw + 2]

                ocr = self.processa_campo(palavra,-1,0,0)
                # print ("ocr: %s (%d %d %d %d)" % (ocr[1],x,y,w,h))
                ##cv2.imshow('palavra',palavra)
                dt_nascto = dt_nascto + " " + ocr[1].replace(' ','')

            ##cv2.imshow('palavras',display_cnt)

            # print ("cpf: %s" % (cpf))
            # print ("dt_nascto: %s" % (dt_nascto))
            cnh.cpf = cpf.strip()
            cnh.dt_nascto = dt_nascto.strip()

            # cv2.waitKey(0)



            #
            # filiacao
            #

            # cv2.destroyAllWindows()

            for x,y in top_left_colsAndRows:
                if y > linha_atual + 40:
                    break

            # print y
            linha_atual = y

            l1 = x
            h1 = y

            #
            # temos que encontrar o ponto direito aproximado em relacao ao esquerdo
            #
            for x,y in top_right_colsAndRows:
                if y >= (linha_atual - 5) and y <= (linha_atual + 5):
                    break

            # print ("linha atual: %d -> right y: %d" % (linha_atual,y))
            r1 = x

            # caso nao encontre o marcador da direita
            if y >= (linha_atual - 5) and y <= (linha_atual + 5):
                h2 = y
            else:
                h2 = linha_atual

            display = np.array(img,copy=True)

            for xprox,yprox in top_left_colsAndRows:
                if yprox > h1 + 150 and yprox <= h1 + 250:
                    break
            altura = yprox - h1 - 10
            # print ("altura %d h1 %d" % (altura,h1))


            cv2.rectangle(display,(l1 + 5,h1),(r1,h2 + altura),(0,0,255),2)

            campo = img[h1 + 10:h2 + altura,l1 + 5:r1]

            campo_ori = np.array(campo,copy=True)

            display_cnt = np.array(campo,copy=True)

            campo = cv2.cvtColor(campo,cv2.COLOR_BGR2GRAY)

            # cv2.imshow('btiwise',campo)

            ret,campo = cv2.threshold(campo,160,255,cv2.THRESH_BINARY_INV)

            campo = self.remove_linha_inferior(campo)
            # cv2.imshow('thresh',campo)


            horizontalSize = 1
            verticalSize = 1
            horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT,(horizontalSize,verticalSize))
            # horizontalStructure [:,0:2] = 0
            # horizontalStructure [:,4:6] = 0
            # print horizontalStructure
            campo = cv2.erode(campo,horizontalStructure,(-1,-1),iterations=1)
            # cv2.imshow('erode',campo)

            horizontalSize = 5
            verticalSize = 1
            horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT,(horizontalSize,verticalSize))
            # horizontalStructure [:,0:2] = 0
            # horizontalStructure [:,4:6] = 0
            # print horizontalStructure
            campo = cv2.dilate(campo,horizontalStructure,(-1,-1),iterations=2)
            # cv2.imshow('dilate',campo)
            # cv2.waitKey(0)


            _,contours,hierarchy = cv2.findContours(campo,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
            # print "Foram encontrados %d contornos" % (len(contours))
            (sorted_contours,boundingBoxes) = self.sort_contours(contours,method='left-to-right')

            ocr = []
            pai = ""
            mae = ""
            pai1 = ""
            pai2 = ""
            mae1 = ""
            mae2 = ""

            linha = 0
            campos = {}
            for idx,cnt in enumerate(sorted_contours):
                x,y,w,h = cv2.boundingRect(cnt)

                area = cv2.contourArea(cnt)

                if area >= 180 and w < 200 and h > 12 and h < 70:
                    cv2.rectangle(display_cnt,(x + 2,y - 1),(x + w - 2,y + h + 1),(10,10,10),1)
                    palavra = campo_ori[y - 1:y + h + 1,x + 2:x + w - 2]
                    ocr = self.processa_campo(palavra,-1,0,0)
                    # print ("y: %d ocr %s" % (y,ocr[1]))
                    linha = y / (campo.shape[0] / 4)

                    # print linha
                    if linha == 0:
                        pai1 = pai1 + (ocr[1].replace(' ','')) + " "
                    elif linha == 1:
                        pai2 = pai2 + (ocr[1].replace(' ','')) + " "
                    elif linha == 2:
                        mae1 = mae1 + (ocr[1].replace(' ','')) + " "
                    elif linha == 3:
                        mae2 = mae2 + (ocr[1].replace(' ','')) + " "



                        # filiacao = filiacao + " " + ocr[1].replace(' ','')
                        # cv2.imshow('palavra',palavra)
                        # cv2.waitKey(0)

            # cv2.imshow('palavras',display_cnt)

            pai = pai1.strip() + pai2
            mae = mae1.strip() + mae2
            # print ("Pai: %s" % (pai))
            # print ("Mae: %s" % (mae))
            cnh.pai = pai.strip()
            cnh.mae = mae.strip()

            # cv2.waitKey(0)



            #
            # permissao
            #

            # cv2.destroyAllWindows()

            for x,y in top_left_colsAndRows:
                if y > linha_atual + 150:
                    break

            # print y
            linha_atual = y
            for xx,yy in top_left_colsAndRows:
                if yy == linha_atual:
                    x = xx  # tenta pegar somente o ultimo x da linha

            l1 = x
            h1 = y

            #
            # temos que encontrar o ponto direito aproximado em relacao ao esquerdo
            #
            for x,y in top_right_colsAndRows:
                if y >= (linha_atual - 5) and y <= (linha_atual + 5):
                    break

            # print ("linha atual: %d -> right y: %d" % (linha_atual,y))
            r1 = x

            # caso nao encontre o marcador da direita
            if y >= (linha_atual - 5) and y <= (linha_atual + 5):
                h2 = y
            else:
                h2 = linha_atual

            r1 = largura_nome

            display = np.array(img,copy=True)

            cv2.rectangle(display,(l1 + 5,h1 + 15),(r1,h2 + 50),(0,0,255),2)

            campo = img[h1 + 15:h2 + 50,l1 + 5:r1]
            campo_ori = np.array(campo,copy=True)

            display_cnt = np.array(campo,copy=True)

            campo = cv2.cvtColor(campo,cv2.COLOR_BGR2GRAY)

            # cv2.imshow('btiwise',campo)

            ret,campo = cv2.threshold(campo,160,255,cv2.THRESH_BINARY_INV)
            campo_thr = np.array(campo,copy=True)
            campo_thr = cv2.bitwise_not(campo_thr,campo_thr)
            # cv2.imshow('thresh',campo)


            horizontalSize = 1
            verticalSize = 1
            horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT,(horizontalSize,verticalSize))
            # horizontalStructure [:,0:2] = 0
            # horizontalStructure [:,4:6] = 0
            # print horizontalStructure
            campo = cv2.erode(campo,horizontalStructure,(-1,-1),iterations=1)
            # cv2.imshow('erode',campo)

            horizontalSize = 5
            verticalSize = 1
            horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT,(horizontalSize,verticalSize))
            # horizontalStructure [:,0:2] = 0
            # horizontalStructure [:,4:6] = 0
            # print horizontalStructure
            campo = cv2.dilate(campo,horizontalStructure,(-1,-1),iterations=2)

            # cv2.imshow('campo nome',campo)


            _,contours,hierarchy = cv2.findContours(campo,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
            # print "Foram encontrados %d contornos" % (len(contours))
            (sorted_contours,boundingBoxes) = self.sort_contours(contours)

            permissao = ""

            for idx,cnt in enumerate(sorted_contours):
                x,y,w,h = cv2.boundingRect(cnt)

                area = cv2.contourArea(cnt)

                # print ("%d %d %d %d (%d, %d)" % (x,y,w,h,campo_ori.shape[0],area))
                if (area >= 180 and w < 200) and (h > 15 and h < 30):
                    cv2.rectangle(display_cnt,(x - 2,y - 2),(x + w + 4,y + h + 2),(10,10,10),1)
                    palavra = campo_ori[y - 2:y + h + 2,x - 2:x + w + 4]
                    ret2,palavra = cv2.threshold(palavra,120,255,cv2.THRESH_BINARY)
                    palavra = cv2.cvtColor(palavra,cv2.COLOR_BGR2GRAY)
                    ocr = self.processa_campo(palavra,-1,0,0)
                    permissao = permissao + " " + ocr[1].replace(' ','')
                    # cv2.imshow('palavra',palavra)

            # cv2.imshow('palavras',display_cnt)

            # print ("permissao: %s" % (permissao))
            cnh.permissao = permissao.strip().replace('H','B').replace('3','B').replace('8','B').replace('4','A')

            # cv2.waitKey(0)


            #
            # registro
            #

            # cv2.destroyAllWindows()

            for x,y in top_left_colsAndRows:
                if y > linha_atual + 50:
                    break

            # print y
            linha_atual = y

            # print ("registro x:  %d" % (x))
            if x > 30:  # provavelmente nao encontramos o marcador da direita (talvez algum campo intermediario
                x = 1

            l1 = x
            h1 = y

            #
            # temos que encontrar o ponto direito aproximado em relacao ao esquerdo
            #
            for x,y in top_right_colsAndRows:
                if y >= (linha_atual - 5) and y <= (linha_atual + 5):
                    break

            # print ("linha atual: %d -> right y: %d" % (linha_atual,y))
            r1 = x

            # caso nao encontre o marcador da direita
            if y >= (linha_atual - 5) and y <= (linha_atual + 5):
                h2 = y
            else:
                h2 = linha_atual

            r1 = largura_nome

            display = np.array(img,copy=True)

            cv2.rectangle(display,(l1 + 5,h1),(r1,h2 + 60),(0,0,255),2)

            campo = img[h1 + 10:h2 + 60,l1 + 5:r1]
            campo_ori = np.array(campo,copy=True)

            display_cnt = np.array(campo,copy=True)

            campo = cv2.cvtColor(campo,cv2.COLOR_BGR2GRAY)

            # cv2.imshow('btiwise',campo)

            ret,campo = cv2.threshold(campo,0,255,cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # cv2.imshow('thresh',campo)

            # campo = remove_linha_inferior(campo)


            horizontalSize = 1
            verticalSize = 1
            horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT,(horizontalSize,verticalSize))
            # horizontalStructure [:,0:2] = 0
            # horizontalStructure [:,4:6] = 0
            # print horizontalStructure
            campo = cv2.erode(campo,horizontalStructure,(-1,-1),iterations=1)
            # cv2.imshow('erode',campo)

            horizontalSize = 6
            verticalSize = 1
            horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT,(horizontalSize,verticalSize))
            horizontalStructure[:,0:2] = 0
            # horizontalStructure [:,4:6] = 0
            # print horizontalStructure
            campo = cv2.dilate(campo,horizontalStructure,(-1,-1),iterations=5)
            # cv2.imshow('campo nome',campo)


            _,contours,hierarchy = cv2.findContours(campo,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
            # print "Foram encontrados %d contornos" % (len(contours))
            (sorted_contours,boundingBoxes) = self.sort_contours(contours)

            registro = ""
            validade = ""
            dt_1_habilitacao = ""
            fx = 0
            fy = 0
            fw = 0
            fh = 0

            for idx,cnt in enumerate(sorted_contours):
                x,y,w,h = cv2.boundingRect(cnt)

                area = cv2.contourArea(cnt)

                # print ("%d %d %d %d (%d, %d)" % (x,y,w,h,campo_ori.shape[0],area))
                if area >= 180 and w < 240 and h > 15 and h < campo_ori.shape[0] - 4:
                    cv2.rectangle(display_cnt,(x + 2,y - 1),(x + w - 2,y + h - 1),(10,10,10),1)
                    palavra = campo_ori[y - 1:y + h - 1,x + 2:x + w - 2]
                    palavra = cv2.cvtColor(palavra,cv2.COLOR_BGR2GRAY)
                    ocr = self.processa_campo(palavra,-1,0,0)

                    if x < 100:
                        registro = registro + " " + ocr[1].replace(' ','')

                    elif x > 100 and x < campo.shape[1] / 2:
                        validade = validade + " " + ocr[1].replace(' ','')
                        fx = x
                        fy = y
                        fw = w
                        fh = h

                    elif x > campo.shape[0] / 2:
                        dt_1_habilitacao = dt_1_habilitacao + " " + ocr[1].replace(' ','')
                        fx = x
                        fy = y
                        fw = w
                        fh = h

                        # print ("registro encontrado em %d %d" % (x,y))
                        # cv2.imshow('palavra',palavra)
                        # cv2.waitKey(0)

            if registro == "":  # vamos tentar forcar o reconhecimento do registro pelo menos

                x = 25
                w = 250
                y = fy - 2
                h = fh + 10

                palavra = campo_ori[y - 1:y + h - 1,x + 2:x + w - 2]
                palavra = cv2.cvtColor(palavra,cv2.COLOR_BGR2GRAY)

                display_cnt = np.array(palavra,copy=True)
                palavra_fc = np.array(palavra,copy=True)

                ret,fc = cv2.threshold(palavra_fc,130,255,cv2.THRESH_BINARY_INV)

                horizontalSize = 2
                verticalSize = 2
                horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT,(horizontalSize,verticalSize))
                horizontalStructure[:,0:2] = 0
                # horizontalStructure [:,4:6] = 0
                # print horizontalStructure
                fc = cv2.dilate(fc,horizontalStructure,(-1,-1),iterations=4)

                horizontalSize = 4
                verticalSize = 1
                horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT,(horizontalSize,verticalSize))
                fc = cv2.dilate(fc,horizontalStructure,(-1,-1),iterations=4)

                # cv2.imshow('thresh',fc)
                # cv2.waitKey(0)

                _,contours,hierarchy = cv2.findContours(fc,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
                # print "Foram encontrados %d contornos" % (len(contours))
                (sorted_contours,boundingBoxes) = self.sort_contours(contours)

                for idx,cnt in enumerate(sorted_contours):
                    x,y,w,h = cv2.boundingRect(cnt)
                    area = cv2.contourArea(cnt)
                    # print ("%d %d %d %d (%d, %d)" % (x,y,w,h,campo_ori.shape[0],area))
                    if (area >= 2000 and w > 180) and (h > 15 and h < 35):
                        cv2.rectangle(display_cnt,(x - 8,y - 5),(x + w - 5,y + h + 7),(10,10,10),1)
                        # cv2.imshow('palavras',display_cnt)
                        # cv2.waitKey(0)

                        palavra_ocr = palavra[y - 5:y + h + 7,x - 8:x + w - 5]
                        ocr = self.processa_campo(palavra_ocr,-1,0,0)
                        registro = registro + " " + ocr[1].replace(' ','')
                        # cv2.imshow('rgistro -f',palavra_ocr)

            # cv2.imshow('palavras',display_cnt)

            # print ("registro: %s" % (registro))
            # print ("validade: %s" % (validade))
            # print ("data 1a habilitacao: %s" % (dt_1_habilitacao))
            cnh.registro = registro.strip().replace('l','1').replace('G','6').replace('B','8').replace('E','8')
            cnh.validade = validade.strip()
            cnh.dt_1a_habilitacao = dt_1_habilitacao.strip()

            # cv2.waitKey(0)

            return cnh

    def resize(self,image,width=None,height=None,inter=cv2.INTER_AREA):
        # initialize the dimensions of the image to be resized and
        # grab the image size
        dim = None
        (h,w) = image.shape[:2]

        # if both the width and height are None, then return the
        # original image
        if width is None and height is None:
            return image

        # check to see if the width is None
        if width is None:
            # calculate the ratio of the height and construct the
            # dimensions
            r = height / float(h)
            dim = (int(w * r),height)

        # otherwise, the height is None
        else:
            # calculate the ratio of the width and construct the
            # dimensions
            r = width / float(w)
            dim = (width,int(h * r))

        # resize the image
        resized = cv2.resize(image,dim,interpolation=inter)

        # return the resized image
        return resized

    def processa_campo(self,campo,y,idx,h):

        params = list()
        params.append(cv2.IMWRITE_PNG_COMPRESSION)
        params.append(0)
        cv2.imwrite('/tmp/cnh_campo.png',campo,params)
        # texto_d = pytesseract.image_to_string(Image.open('/tmp/cnh_campo.png'),config='-psm 7 digits')
        texto_d = -1  # nao estou usando por enquanto - melhoria na performance
        texto_c = pytesseract.image_to_string(Image.open('/tmp/cnh_campo.png'),config='-psm 6 -l por')

        # cv2.imwrite('/tmp/cnh_campo.tif',campo)
        # texto_d = pytesseract.image_to_string(Image.open('/tmp/cnh_campo.tif'),config='-psm 7 digits')
        # texto_d = -1 # nao estou usando por enquanto - melhoria na performance
        # texto_c = pytesseract.image_to_string(Image.open('/tmp/cnh_campo.tif'),config='-psm 8 -l por+spa+eng+ita+jpn ')
        # texto_c = pytesseract.image_to_string(Image.open('/tmp/cnh_campo.tif'),config='-psm 8 -l por ')


        # print "Campo ---> idx: %d y: %d h: %d [%s][%s:%d] " % (idx,y,h,texto_d,texto_c,len(texto_c))

        return [texto_d,texto_c]

    def processa_cnh(self):

        # img = scipy.ndimage.interpolation.rotate(img,270.0)
        # img = cv2.resize (img,(612,816))
        img = cv2.resize(self.img,(816,612))

        cv2.imwrite('/tmp/img_cnh.png',img)

        # img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

        img_display,top_left_colsAndRows = self.find_corner(img, 'top_left')
        img_display,top_right_colsAndRows = self.find_corner(img_display, 'top_right')

        # print top_left_colsAndRows
        # top_left_colsAndRows = order_corners (top_left_colsAndRows)
        # top_right_colsAndRows = order_corners (top_right_colsAndRows)
        # print top_left_colsAndRows

        img = self.remove_doc(img,top_left_colsAndRows,top_right_colsAndRows)

        # apos remover o centro, refaz os corners para atualizar numero de linhas e colunas
        img_display,top_left_colsAndRows = self.find_corner(img,'top_left',doc=True)
        img_display,top_right_colsAndRows = self.find_corner(img_display,'top_right',doc=True)

        # print top_left_colsAndRows
        top_left_colsAndRows = self.order_corners(top_left_colsAndRows)
        top_right_colsAndRows = self.order_corners(top_right_colsAndRows)
        # print top_left_colsAndRows

        cnh = self.encontra_campos(img,top_left_colsAndRows,top_right_colsAndRows)

        print ("==========================================================")
        print ("Nome:              %s" % (cnh.nome))
        print ("RG:                %s" % (cnh.rg))
        print ("CPF:               %s" % (cnh.cpf))
        print ("DT Nascto:         %s" % (cnh.dt_nascto))
        print ("Pai:               %s" % (cnh.pai))
        print ("Mae:               %s" % (cnh.mae))
        print ("Permissao:         %s" % (cnh.permissao))
        print ("Registro:          %s" % (cnh.registro))
        print ("DT Validade:       %s" % (cnh.validade))
        print ("DT 1a Habilitacao: %s" % (cnh.dt_1a_habilitacao))
        print ("==========================================================")

        return cnh


if __name__ == "__main__":

    # Read the images from the file
    # img = cv2.imread('/home/tercio/projects/projects_cm/CM/DocReader/Imagens/cnh_tercio_scanner.jpg')
    # img = scipy.misc.imread ('/home/tercio/projects/projects_cm/CM/DocReader/Imagens/cnh_marcia.png')
    # img = scipy.misc.imread ('/home/tercio/projects/projects_cm/CM/DocReader/Imagens/cnh.jpg')
    # img = scipy.misc.imread ('/home/tercio/projects/projects_cm/CM/DocReader/Imagens/cnh_dj.jpg')

    # img = scipy.misc.imread ('/home/tercio/projects/projects_cm/CM/DocReader/Imagens/cnh8.jpg')


    for i in range(1,14):
        # if i == 4:
        #	continue # pulando os que estao quebrando o loop por enquanto

        img = cv2.imread('/home/tercio/projects/projects_cm/CM/DocReader/Imagens/cnh%d.jpg' % (i),1)

        print ("Processando: cnh%d.jpg\n" % (i))

        cv2.destroyAllWindows()
        cv2.imshow('cnh',img)
        cv2.moveWindow('cnh',650,200)
        cv2.waitKey(0)

    cnh_reader = CnhReader("FRENTE",img)
    cnh = cnh_reader.processa_cnh()

    # for attr in dir(cnh):
    #	print "CNH.%s = %s" % (attr, getattr(cnh, attr))

    try:
        print ("Nome:              %s" % (cnh.nome))
        print ("RG:                %s" % (cnh.rg))
        print ("CPF:               %s" % (cnh.cpf))
        print ("DT Nascto:         %s" % (cnh.dt_nascto))
        print ("Pai:               %s" % (cnh.pai))
        print ("Mae:               %s" % (cnh.mae))
        print ("Permissao:         %s" % (cnh.permissao))
        print ("Registro:          %s" % (cnh.registro))
        print ("DT Validade:       %s" % (cnh.validade))
        print ("DT 1a Habilitacao: %s" % (cnh.dt_1a_habilitacao))
    except AttributeError:
        print "erro lendo o documento..."

    cv2.waitKey(0)

    print ("\n--------------------------------------------------------------------\n")
