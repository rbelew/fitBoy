''' initMove_v0:  load initial Movement objects
Created on Jul 3, 2017

@author: rik
'''

import csv 
import json 

from moveGen.models import Assessment, CardioPattern,Movement, MoveSeq
from django.core.management.base import BaseCommand

# jewels updated 18 Sept 17

Move1 = {'C': 'Assault Bike',
	'LS': 'Split Squat',
	'MS': 'TB Deadlift',
	'Pull': 'Pull-Up',
	'Push': 'Push-Up',
	'St': 'Turkish Get-Up' }

Assess1= {'C': ['Max Cal Assault Bike', '5 min'],
	'LS': ['Split Squat', '3x8 per leg', '35/50#'],
	'MS': ['TB DL (2 rm/bw)'],
	'Pull': ['Pull-Up', '3x8', '3x4'],
	'Push': ['Push-Up', '3x16', '3x8'],
	'St': ['TGU 2rm/arm', 'both arms, up and down'] }

Move2 = {'BiLat': 'St-Sp, BiLateral',
	'CCPull': 'Closed Chain Pull',
	'Endur': 'Endurance (3min+)',
	'FBCP': 'Full Body/Compound/Cyclical Pulls',
	'FRCOCLL': 'FRC/Open Chain Lower Leg',
	'FRCX': 'Extra FRC (hi-tension)',
	'Gly': 'Glycolytic (~1min)',
	'HH': 'Hip Hinge',
	'Hang': 'Hanging',
	'LC': 'Loaded Carry',
	'OCCC': 'Open Chain Core Conditioning',
	'OCPr': 'Open Chain Press',
	'PPAR': 'Push/Pull/Anti-Rotation',
	'PhCr': 'PhCr (>15sec)',
	'Plank': 'Plank',
	'Rest': 'Rest',
	'SLS': 'Strength-Speed; SL-BiLateral',
	'TBDL': 'TB DL (submax effort, concentric only)',
	'UBPlyo': 'Strength-Speed; UB Plyo+Compound' }

Move2to1 = {'BiLat': 'LS',
	'CCPull': 'Pull',
	'Endur': 'C',
	'FBCP': 'MS',
	'FRCOCLL': 'LS',
	'FRCX': 'St',
	'Gly': 'C',
	'HH': 'MS',
	'Hang': 'Pull',
	'LC': 'St',
	'OCCC': 'St',
	'OCPr': 'Push',
	'PPAR': 'Pull',
	'PhCr': 'C',
	'Plank': 'Push',
	'Rest': 'C',
	'SLS': 'LS',
	'TBDL': 'MS',
	'UBPlyo': 'Push' }

A2Seq = {'LS': ['MS','Push','Pull','St'],
	'MS': ['Push','Pull','St','LS',],
	'St': ['Pull','Push','LS','MS'],
	'Pull': ['LS','MS','Push','St'],
	'Push': ['LS','MS','Pull','St']	 }


# Pattern across weeks of meso
# CardioPatterns = {'LowEndurance': ['PhCr','PhCr','PhCr','Gly','Gly','Gly','Endur'],
# 				  'HighEndurance': ['Endur','PhCr','Endur','Gly','Endur','PhCr','Endur'] }

# file to load
CardioTemplateDir = 'CardioTemplates/'
CardioPatterns = {'LowEndurance': 'LowEndurance.csv',
				  'HighEndurance': 'HighEndurance.csv',
				  'GlycoEmphasis': 'GlycolyticEmphasis.csv' }
MaxCardioDay = 4
MaxCardioWeek = 16

# choices given previous day's cardio
SecondaryCardio = {'PhCr': 'Endur', 
					'Gly': 'Endur', 
					'Endur': 'Gly'}

class Command(BaseCommand):

	help = 'load initial Movements, A2Seq, CardioPatterns, ...'

	def add_arguments(self, parser):
		parser.add_argument('dataDir',nargs='?')

	def handle(self, *args, **kwargs):
		dataDir = kwargs['dataDir']
		
		print('initMove: dataDir=%s...' % (dataDir) )

		CardioPattern.objects.all().delete()
		Movement.objects.all().delete()
		MoveSeq.objects.all().delete()
		
		for id,name in Move1.items():
			m1 = Movement(name=name, mtype='Measure')
			m1.abbrev = id
			m1.cardio = (id=='C')
			m1.save()

		print('initMove: Measures done. NMovement=%d' % (Movement.objects.all().count()) )
		
		for m1id,assList in Assess1.items():
			m1name = Move1[m1id]
			try:
				m1 = Movement.objects.get(name=m1name)
			except Exception as e:
				print ('initMove: nonunique1 Movement name %s ?!' % (m1name) )
				continue
			for aname in assList:
				a = Assessment(name=aname)
				a.move = m1
				a.save()

		print('initMove: Assessment done. NAssessment=%d' % (Assessment.objects.all().count()) )

		for m2id,m1id in Move2to1.items():
			name2 = Move2[m2id]
			m2 = Movement(name=name2,mtype='Accessory')
			m1name = Move1[m1id]
			m2.abbrev = m2id
			try:
				m1 = Movement.objects.get(name=m1name)
			except Exception as e:
				print ('initMove: nonunique2 Movement name %s ?!' % (m1name) )
				continue
			m2.parent = m1
			m2.save()

		print('initMove: Accessory done. NMovement=%d' % (Movement.objects.all().count()) )
			
		egFile = dataDir + 'pgExamples_171220.csv'
		reader = csv.DictReader(open(egFile))
		for i,entry in enumerate(reader):
			# Move2,EgIdx,ExampleName
			# idx = int(entry['EgIdx'])
			name3 = entry['ExampleName']
			m3 = Movement(name=name3,mtype='Exercise')
			try:
				m2name = Move2[entry['Move2']]
				m2 = Movement.objects.get(name=m2name)
			except Exception as e:
				print ('initMove: nonunique3 Movement name %s ?!' % (entry['Move2']) )
				continue
			
			m3.parent = m2
			m3.save()

		print('initMove: Exercise done. NMovement=%d' % (Movement.objects.all().count()) )

		a2seqFull = {}
		for m1id,m2List in A2Seq.items():
			m2FullList = []
			for m2id in m2List:
				m2FullList.append(Move1[m2id])
			a2seqFull[Move1[m1id]] = m2FullList
		ms = MoveSeq(name='default')
		# ms.json = json.dumps(a2seqFull)
		ms.json = a2seqFull
		ms.save()
		
		print('initMove: MoveSeq: %s' % (ms.json) )
		
		# ASSUME weeks numbered, arbitrary number of days
		# NB: need to have same dimensions for all CardioPatterns!
		for cp,cpFileName in CardioPatterns.items():
			cp = CardioPattern(name=cp)
			csched = {}
			reader = csv.reader(open(dataDir+CardioTemplateDir+cpFileName))
			for i,row in enumerate(reader):
				# drop header
				if i==0: continue
				
				wkSched = {}
				# wkIdx = int(row[0])
				for j,day in enumerate(row[1:]):
					# NB: need to increment j index because skipping weekIdx
					name2 = Move2[ row[j+1] ]
					try:
						m = Movement.objects.get(name=name2)
					except Exception as e:
						print ('initMove: Cardio %s %d %d unknown Move name %s ?!' % (cp,i,j,name2) )
						continue
					wkSched[j]=m.pk
					# print ('initMove: Cardio %s %d %d Move name %s m.pk=%s ' % (cp,i,j,name2,wkSched[j]) )
				
				# import pdb; pdb.set_trace()
					
				nspecDay = len(wkSched)
				for j2 in range(MaxCardioDay - nspecDay):
					wkSched[nspecDay+j2]=None
					
				# NB: zero-indexed weeks
				csched[i-1] = wkSched

				print ('initMove: Cardio %s %d wkSched=%s ' % (cp,i,csched[i-1]) )
			
			nspecWeek = len(csched)
			for i in range(MaxCardioWeek-nspecWeek):
				wkSched = {}
				for j in range(MaxCardioDay):
					wkSched[j]=None
				# NB: zero-indexed weeks
				csched[nspecWeek+i] = wkSched
				
			# cp.schedule = json.dumps(csched)
			
			print(cp, csched)
			cp.schedule = csched
			
			cp.save()
			# ASSUME all rows of same length
						
			print ('initMove: Cardio %s pk=%d read %d x %d' % (cp,cp.pk,nspecDay, nspecWeek) )	

		print('initMove: CardioPatterns: %s' % (CardioPattern.objects.all().count() ))	
		