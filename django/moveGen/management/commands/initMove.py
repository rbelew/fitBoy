''' initMove:  load initial MesoSystem Movement objects
Created on 180616

	
@author: rik
'''

import json 

from moveGen.models import MesoSystem, Movement
from moveGen.views import moves2dict
from django.core.management.base import BaseCommand 
from django.core import serializers

class Command(BaseCommand):
 
	help = 'load initial MesoSystem Movement objects'
 
# 	def add_arguments(self, parser):
# 		parser.add_argument('dataDir',nargs='?')
 
	def handle(self, *args, **kwargs):
		
		# local:
		# dataDir = '/Data/whbFit/fitAlchem/' # kwargs['dataDir']
		# Webfaction:
		dataDir = '/home/rik/webapps/djstatic/fitAlchem/'

		print('initMesoSys: dataDir=%s...' % (dataDir) )

		moveList = json.load(open(dataDir+'allMoves_180617.json'))

		moveDict = moves2dict(moveList)
		
# 		print(moveDict)
# 		print('here')
# 		import pdb; pdb.set_trace()

		sys = MesoSystem()
		sys.name = 'default'
		sys.author = 'admin'
		# NB: Only need moveDict[0]
		sys.moveDict = moveDict[0]
		sys.save()

		