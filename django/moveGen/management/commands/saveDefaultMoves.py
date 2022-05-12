''' saveDefaultMoves:  serialized all Movement objects with PARENT cached in
						for use as initialization for MesoSystem
Created on 180617

2do 17 Jun 18: use django-serializable-model  BUT
	https://github.com/agilgur5/django-serializable-model
	Will have some problems with Django 2.0 as the Manager's use_for_related_fields has been removed.


	User.objects.prefetch_related('post_set').get(pk=new_user.pk).serialize('post_set')
	Movement.objects.prefetch_related('parent').get(pk=move.pk).serialize('parent')
	
	or perhaps DRF rest-framework-generic-relations
 	to serialize PARENTS correctly

	
@author: rik
'''

import json 

from moveGen.models import Movement

from django.core.management.base import BaseCommand 

class Command(BaseCommand):
 
	help = 'serialized all Movement objects with PARENT cached in'
 
# 	def add_arguments(self, parser):
# 		parser.add_argument('dataDir',nargs='?')
 
	def handle(self, *args, **kwargs):
		
		# local:
		dataDir = '/Data/whbFit/fitAlchem/' # kwargs['dataDir']
		# Webfaction:
		# dataDir = '/home/rik/webapps/djstatic/fitAlchem/'
		
		print('saveDefaultMoves: dataDir=%s...' % (dataDir) )
		
		moveList = []
		allMovesQS = Movement.objects.all()
		for mo in allMovesQS:
			mdict = {'idx': mo.idx, 
					'name': mo.name, 
					'mtype': mo.mtype,
					'task': mo.task }
			if mo.parent == None:
				mdict['parent'] = None
			else:
				po = mo.parent
				pdict = {'idx': po.idx, 
						'name': po.name, 
						'mtype': po.mtype,
						'task': po.task }
				mdict['parent'] = pdict
			moveList.append(mdict)
		
		moveList.sort(key=lambda d: d['idx'])
		
		outf = dataDir + 'allMoves_180617.json'
		json.dump(moveList,open(outf,'w'),indent=1)
		
		

		
