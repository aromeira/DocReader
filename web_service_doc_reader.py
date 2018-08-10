#!/usr/bin/python

import importlib

from twisted.web import server, resource, static
from twisted.internet import reactor,threads
import cgi

import cv2
import numpy as np
import scipy.io
import scipy.misc
import datetime
import time
import os
import glob

import time
import random

import unicodedata

import MySQLdb
import captcha_db

import mapper

import sys
import traceback

#
# -----------------------------------
#


MAX_LOCAL_TRY = 3

captcha_server = "10.1.12.22"
captcha_port   = 10080

image_path = "./upload/"


def createResponse (request,engine="",captcha="",status=999,token="NA",img_url="",tempo=0.0,msg=""):

	html = """
<html>
<head>
<style>
captcha {visibility:hidden;display:none;}

token{visibility:hidden;display:none;}

status{visibility:hidden;display:none;}
msg{visibility:hidden;display:none;}

</style>

<script>
function error () {
  status = document.getElementsByTagName("status")[0].innerHTML;
  status = status + 0;
  imagem = document.getElementById ("imagem");
  imagem_url = document.getElementById ("imagem_url");
  captcha_text = document.getElementById("captcha_text");
  if (status != 0) {
	  imagem.hidden = true;
	  imagem_url.hidden = true;
	  captcha_text.hidden = true;
  }
}
</script>

</head>
<body onload=error();>
<captcha>%s</captcha>
<status>%d</status>
<msg>%s</msg>
<token>%s</token>

<h1 style='background-color:#cccccc;'>C&M Captcha Decoder  -  (Engine: %s)</h1>

<h2 style="color:#ff0000">%s</h2>

<h3 id=imagem>Imagem Recebida: </h3> <img id=imagem_url src=/upload/%s >
<h2 id=captcha_text>Captcha : %s</h2>
<hr>Tecnologias utilizadas: Python, NumPy, SciPy, Twisted, MySQLdb, MySQL e OpenCV<br>Tempo do processamento: %f em milisegundos
</body>
</html>
"""
	return (request,html % (captcha,status,msg,token,engine,msg,img_url,captcha,tempo))


class DecoderResource(resource.Resource):

	numberRequests = 0


	def printResult (self,args):
		(request,html) = args
		request.write (html)
		request.finish()
	

	def render_POST(self, request):

		d = threads.deferToThread(self.decodeCaptcha,request)
		d.addCallback (self.printResult)
		return server.NOT_DONE_YET
	
	#
	# Processamento do Captcha
	#
	def decodeCaptcha (self, request):



		try:

			start = datetime.datetime.now()

			#self.numberRequests += 1
			request.setHeader("content-type", "text/html")

			file_jpg = "captcha_" + str(random.random()) + str(time.time()) + ".jpg"
			#file_jpg = "teste_twisted.jpg"
			filename = image_path + file_jpg

			#print request.args
			try:

				if len(request.args['data'][0]) == 0:
					return createResponse (request,"","",300,"NA","",0.0,"Imagem nao enviada ou fora do padrao")

				fd = open (filename,"w")
				fd.write(request.args['data'][0])
				fd.close()
				print "arquivo gerado..."

			except KeyError, IOError:
				return createResponse (request,"","",300,"NA","",0.0,"Imagem nao enviada ou fora do padrao")


			np.seterr (over='ignore')

			src_gray = scipy.misc.imread(filename)
			ori = scipy.misc.imread(filename)


			try:
				tmp_eng = request.args['engine'][0]

				if tmp_eng in mapper.mapper:
					engine = mapper.mapper[tmp_eng]
				else:
					engine = tmp_eng
				print "engine: %s " % engine

			except KeyError:
				return createResponse (request,"","",200,"NA","",0.0,"Engine nao informado! Por favor especifique o engine desejado.")


			try:
				counter = int (request.args['counter'][0])
				print "counter: %d" % counter

			except KeyError:
				counter = 1

			try:

				#
				# Se o counter for maior que o limite, fara o fallback para o DBC
				#
				if counter > MAX_LOCAL_TRY:
					engine = "max_try_reached"

				decoder = importlib.import_module(engine)

				(src_gray,ori) = decoder.preprocessamento (src_gray,ori)

				imgs =  decoder.segmentacao (src_gray,ori)

				# tenho que tirar esse if fora. Tenho que adicionar os dois parametros extras
				# como parametros opcionais em todos os decoder.reconhecimento() dos engines
				if engine == "recaptcha":

					#try:
					#	if len(request.args['banner'][0]) == 0:
					#		return createResponse (request,"","",300,"NA","",0.0,"Banner nao enviado ou fora do padrao")
					#
					#	bfile_jpg = "banner_" + str(random.random()) + str(time.time()) + ".jpg"
					#	bfilename = image_path + bfile_jpg

					#	fd = open (bfilename,"w")
					#	fd.write(request.args['banner'][0])
					#	fd.close()
					#	print "arquivo (banner) gerado..."

					#except KeyError, IOError:
					#	return createResponse (request,"","",300,"NA","",0.0,"Banner nao enviado ou fora do padrao")

					# banner text	
					try:
						banner_text = request.args['banner_text'][0]

					except KeyError:
						return createResponse (request,"","",200,"NA","",0.0,"Banner_text nao informado.")

					# grid
					try:
						grid  = request.args['grid'][0]

					except KeyError:
						return createResponse (request,"","",200,"NA","",0.0,"grid nao informado.")


					#captcha = decoder.reconhecimento (filename,bfilename,banner_text,grid)
					captcha = decoder.reconhecimento (filename,banner_text,grid)
					print "CAPTCHA %s solved: %s" % (captcha["captcha"], captcha["text"])
					token_dbc = int(captcha['captcha'])
					captcha = captcha["text"]
					captcha = unicodedata.normalize('NFKD', captcha).encode('ascii','ignore')

					stop = datetime.datetime.now()

					print captcha

					c = stop - start
					milliseconds = (c.days * 24 * 60 * 60 + c.seconds) * 1000 + c.microseconds / 1000.0

					token = captcha_db.logToDB (engine,captcha,milliseconds,file_jpg,token_dbc)
	
				else:
					captcha = decoder.reconhecimento (imgs)


					stop = datetime.datetime.now()

					print captcha

					c = stop - start
					milliseconds = (c.days * 24 * 60 * 60 + c.seconds) * 1000 + c.microseconds / 1000.0

					token = captcha_db.logToDB (engine,captcha,milliseconds,file_jpg)

				return createResponse (request,engine,captcha,0,token,file_jpg,milliseconds,"OK")


			except ImportError, e:


				print "chamando o DBC... %s" % (e)

				import dbc

				(captcha,partnerId) = dbc.decode(filename)
		
				captcha = unicodedata.normalize('NFKD', captcha).encode('ascii','ignore')
				#print type(captcha)
				
				print captcha

				stop = datetime.datetime.now()
				c = stop - start
				milliseconds = (c.days * 24 * 60 * 60 + c.seconds) * 1000 + c.microseconds / 1000.0


				# salvar o arquivo com o engine + valor do captcha retornado para gerar massa de dados
				# o REFUND, caso usado tera que renomear para _erro ou algo parecido para nao usarmos 
				# arquivos com valores errados


				newfile = "captcha_" + engine + "-" + captcha + "-" + str(time.time()) + ".jpg"
				newfilename = image_path + "captcha_" + engine + "-" + captcha + "-" + str(time.time()) + ".jpg"

				os.rename (filename,newfilename)

				token = captcha_db.logToDB ("dbc",captcha,milliseconds,newfile,partnerId)

				return createResponse (request,"dbc",captcha,0,token,newfile,milliseconds,"OK - Fallback para DBC - api externa")

		except Exception as e:
			#import dbc
			#print "no exception ! ! ! "
			#err = dbc.decode(filename)

			#print "DBC Error string : %s" % (err)
			return createResponse (request,"","",900,"NA","",0,"Erro nao identificado! %s : %s %s (DBC string de erro: %s)" % (e.__class__.__name__,e,traceback.format_exc(),""))


	#
	# Mostra uma tela inicial em caso de GET para que o usuario possa testar o sistema
	# Existe a opcao de se mandar o captcha para os diferentes engines suportados pela C&M quanto
	# para os DBC
	#
	def render_GET (self,request):

		html = """<html><body><h1 style='background-color:#cccccc;'>C&M Captcha Decoder</h1>
				  <form action="" method="post" enctype="multipart/form-data">
							  Escolha a imagem do captcha:  <input type="file" name="data" />

								  <br><br>Escolha o tipo do Captcha (engine a ser utilizado):<br>
								  Cadin : <input type=radio name=engine  value=cadin><br>
								  Cadesp : <input type=radio name=engine  value=cadesp><br>
								  Receita : <input type=radio name=engine  value=receita><br>
								  Receita (out/2015): <input type=radio name=engine  value=receita_v7><br>
								  Jucesp : <input type=radio name=engine  value=jucesp><br>
								  INSS (prev. social) : <input type=radio name=engine  value=inss><br>
								  Teste de nao implementado : <input type=radio name=engine  value=xxxxx> fara o fallback para DBC<br>
								  OCR : <input type=radio name=engine  value=ocr>Para captchas muito simples que nao precisam de pre-processamento<br>
								  Detran SP : <input type=radio name=engine  value=detransp><br>
								  reCaptcha : <input type=radio name=engine  value=recaptcha><br>
								  <!-- &nbsp; - reCaptcha: Escolha a imagem do banner:  <input type="file" name="banner" /><br> -->
								  &nbsp; - reCaptcha: Digite o texto:  <input type="text" name="banner_text" /><br>
								  &nbsp; - reCaptcha: Grid:  <input type="text" name="grid" /><br>

								  Contador: <input type=text name=counter value=1> (Serve para, baseado em um limite interno, enviar o request para o DBC - O provedor deve informar esse dado)
								  <br><br>
								  <input type="submit" value="Enviar" />

								  <br><br><hr>Tecnologias utilizadas: Python, NumPy, SciPy, Twisted, MySQLdb, MySQL e OpenCV

				   </form></body></html>
				""" # % (captcha_server,captcha_port)
		return html



#
# url para processamento da opcao de refund do sistema. O Status do captcha no DB sera
# alterado 
#
class RefundResource(resource.Resource):

	numberRequests = 0


	def render_GET(self, request):

		request.setHeader("content-type", "text/html")

		print "refund : %s" % (request.args)
		try:
			token = request.args['token'][0]
		except KeyError:
			return "Parametro token nao especificado"

		try:
			(filename,partner_id,captcha) = captcha_db.refund(token)

			print filename
			print partner_id
			#print "filename from DB: %s" % rc;
			ori = image_path + filename

			newfilename = filename
			newfilename = newfilename.replace("captcha","captcha-bad")
			newfilename = image_path + newfilename


			#print ori
			#print newfilename
			print "refund: partnerid: %d" % (partner_id)

			import dbc
			dbc.refund(captcha,partner_id)
			
			os.rename (ori,newfilename)

			return "<status>0</status><msg>OK</msg>"

		except Exception as e:
			return "Erro!<status>99</status><msg>Erro no refund: %s/msg>" % (e)



class StatsResource(resource.Resource):

	numberRequests = 0


	def render_GET(self, request):

		request.setHeader("content-type", "text/html")

		try:
			dt_inicial = request.args['dt_inicial'][0]
			dt_final = request.args['dt_final'][0]

			json = captcha_db.stats(dt_inicial,dt_final)
			return json

		except:
			pass

		json = captcha_db.stats()


		try:
			fd = open ("./cm_captcha_web_server.html","r")
			html = fd.read()
			fd.close ()

			return html % json

		except IOError, e:
			return "Erro processando a saida : %s" % e



os.chdir ('/opt/cmsoftware/captcha')

root = resource.Resource()

root.putChild("", DecoderResource())
root.putChild("refund", RefundResource())
root.putChild("upload", static.File("./upload"))
root.putChild("resources", static.File("./resources"))
root.putChild("stats", StatsResource())

factory = server.Site(root)
reactor.listenTCP(captcha_port, factory)
reactor.run()
