import cv2
import unicodedata
import json
import argparse
import threading
import time
from twocaptcha import CaptchaUpload

#INPUTS = None
#parser = argparse.ArgumentParser()

CNH_FRENTE = {'resize': (800,570),
              'crops': {'nome': {'y1': 136,'y2': 171,'x1': 116,'x2': 774},
                        'rg': {'y1': 198,'y2': 228,'x1': 400,'x2': 774},
                        'cpf': {'y1': 256,'y2': 287,'x1': 400,'x2': 498},
                        'dt_nasc': {'y1': 256,'y2': 295,'x1': 620,'x2': 780},
                        'num_reg': {'y1': 535,'y2': 566,'x1': 122,'x2': 382},
                        'dt_val': {'y1': 535,'y2': 566,'x1': 393,'x2': 574},
                        'dt_ini': {'y1': 535,'y2': 566,'x1': 586,'x2': 775},
                        'cod_nac': {'y1': 317,'y2': 598,'x1': 57,'x2': 110},
                        }
              }

CNH_VERSO = {'resize': (800,570),
             'crops': {'obs': {'y1': 37,'y2': 212,'x1': 118,'x2': 766},
                       'local': {'y1': 348,'y2': 376,'x1': 118,'x2': 576},
                       'dt_emissao': {'y1': 348,'y2': 376,'x1': 590,'x2': 766},
                       'num_renach': {'y1': 435,'y2': 472,'x1': 622,'x2': 785},
                       }
             }

RG_FRENTE = {'resize': (800,570),
             'crops': {'orgao_emissor': {'y1': 0,'y2': 0,'x1': 0,'x2': 0},
                       }
             }

'''RG_FRENTE = {'resize': (800,570),
             'crops': {'orgao_emissor': {'y1': 71,'y2': 93,'x1': 270,'x2': 653},
                       'uf_emissor': {'y1': 40,'y2': 71,'x1': 308,'x2': 620},
                       }
             }'''

''' ROBSON
RG_VERSO = {'resize': (800,570),
            'crops': {'rg': {'y1': 52,'y2': 101,'x1': 138,'x2': 468},
                      'dt_emissao': {'y1': 48,'y2': 103,'x1': 566,'x2': 864},
                      'nome': {'y1': 103,'y2': 163,'x1': 138,'x2': 864},
                      'nome_pai': {'y1': 163,'y2': 222,'x1': 138,'x2': 864},
                      'nome_mae': {'y1': 222,'y2': 301,'x1': 138,'x2': 864},
                      'naturalidade': {'y1': 327,'y2': 380,'x1': 36,'x2': 570},
                      'dt_nasc': {'y1': 327,'y2': 370,'x1': 570,'x2': 864},
                      'doc_origem': {'y1': 384,'y2': 424,'x1': 166,'x2': 864},
                      'cpf': {'y1': 485,'y2': 540,'x1': 85,'x2': 530},
                      }
            }
'''

#DAY
RG_VERSO = {'resize': (800,570),
            'crops': {'rg': {'y1': 38,'y2': 82,'x1': 150,'x2': 500},
                      'dt_emissao': {'y1': 34,'y2': 82,'x1': 610,'x2': 866},
                      'nome': {'y1': 82,'y2': 140,'x1': 147,'x2': 866},
                      'nome_pai': {'y1': 140,'y2': 193,'x1': 147,'x2': 866},
                      'nome_mae': {'y1': 193,'y2': 252,'x1': 147,'x2': 866},
                      'naturalidade': {'y1': 290,'y2': 345,'x1': 50,'x2': 589},
                      'dt_nasc': {'y1': 290,'y2': 345,'x1': 589,'x2': 866},
                      'doc_origem': {'y1': 341,'y2': 381,'x1': 575,'x2': 866},
                      'cpf': {'y1': 439,'y2': 596,'x1': 90,'x2': 471},
                      }
            }


confDoc = {'CNH_FRENTE': CNH_FRENTE,
           'CNH_VERSO': CNH_VERSO,
           'RG_FRENTE': RG_FRENTE,
           'RG_VERSO': RG_VERSO}

outputs = {}


class twoCaptchaSolver(threading.Thread):
    print ("ToCaptcha")

    def __init__(self,key,img):
        threading.Thread.__init__(self)
        self.key = key
        self.imagem = img

    def run(self):
        ini = time.time()
        pathfile = "/home/danielle/projects/python/pyParseDocts/data/{}_{}.jpg".format(self.key,
                                                                                      str(round(time.time() * 1000)))
        cv2.imwrite(pathfile,self.imagem)
        twocap = CaptchaUpload()
        outputs[self.key] = twocap.solve(pathfile)
        # print(twocap.solve(pathfile))
        print("parse {} -- Tempo = {}".format(self.key,time.time() - ini))
        print(outputs[self.key])

        if (outputs[self.key] == 1 or outputs[self.key] == None):
            print ("Erro na obtencao do campo [" + self.key + "]")

        print("===============================================")
        #print(dict(outputs))


class DocReader():
    def __init__(self,tipo_doc,lado_doc,arr_doc,tipoResponse="json"):

        self.tipo_doc = tipo_doc
        self.lado_doc = lado_doc
        self.img = arr_doc

        print('TIPO_DOC [' + self.tipo_doc + '_' + self.lado_doc + ']')
        #print(type(self.img))

    def cropDoc(self):

        doc = confDoc[self.tipo_doc + '_' + self.lado_doc]
        resize = doc['resize']
        crops = doc['crops']

        '''realiza o crop dos campos do documento
         e gera os arquivos para enviar para o 2Captcha'''
        threads = []
        for key in crops.keys():
            ci = crops[key]
            print (ci)
            try:

                cv2.imwrite("/home/danielle/projects/python/pyParseDocts/data/" + key + '.jpg',
                            self.img[ci['y1']:ci['y2'],ci['x1']:ci['x2']])

                outputs.clear()
                thread = twoCaptchaSolver(key,self.img[ci['y1']:ci['y2'],ci['x1']:ci['x2']])
                thread.start()
                threads.append(thread)

            except:
                print ("Erro Thread: Nao foi realizado o parse do campo {}".format(key))

        for thread in threads:
            thread.join()

        return json.dumps(outputs)


# executa testes caso nao seja inicializado a classe por solicitacao
if __name__ == '__main__':
    ini = time.time()

    # setArgs()
    # INPUTS, unparsed = parser.parse_known_args()
    # respNav = ScrapDoc()
    # print( respNav.parseDoc())
    # print( "tempo = {}".format(time.time()-ini))
