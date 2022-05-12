''' progGen: fitness program generator

Created on May 29, 2017

@author: rik
'''

from collections import defaultdict

import csv 
import random 

import jinja2

# Constants

Move1 = {'LS': 'Leg Strength',
			'MS': 'Max Strength',
			'ST': 'Stabilize',
			'Push': 'Push',
			'Pull': 'Pull',
			'C': 'Cardio'}

Assess1= {'LS': ['Split Squat', '3x8 per leg', 'rx/rx#'], 
			'MS': ['TB DL (1 rm/bw)'], 
			'Push': ['Push Up', '3x16', '3x8'], 
			'Pull': ['Pull Up', '3x8', '3x4'], 
			'ST': ['TGU 2rm/bw', 'both arms, up and down'], 
			'C': ['Max Cal Assault Bike', '5 min'] }

Move2 = {'FRCOCLL': 'FRC/Open Chain Lower Leg', 
		'SLS': 'Single Leg Stability', 
		'BiLat': 'Strength - Speed ; SL - BiLateral', 
		'TBDL': 'submax effort TB DL (concentric only)', 
		'Plank': 'Plank', 
		'OCPr': 'Open Chain Press', 
		'UBPlyo': 'Strength - Speed ; UB Plyo + Compound', 
		'OCPull': 'Open/Closed Chain Pull', 
		'PP': 'Push/Pull', 
		'FBCCP': 'Full Body/Compound/Cyclical Pulls', 
		'TGULC': 'Turkish Get-Up/Loaded Carry', 
		'FRCX': 'Extra FRC (hi-tension) work', 
		'OCCC': 'Open Chain Core Conditioning', 
		'PhCr': 'PhCr (>15sec)', 
		'Gly': 'Glycolytic (~1min)', 
		'Endur': 'Endurance (3min+)'}

A2Seq = {'LS': ['MS','Push','Pull','ST'],
			'MS': ['LS','Push','Pull','ST'],
			'ST': ['LS','MS','Push','Pull'],
			'Push': ['LS','MS','Pull','ST'],
			'Pull': ['LS','MS','Push','ST'] }

Move2to1 = {'FRCOCLL': 'LS', 
			'SLS': 'LS', 
			'BiLat': 'LS', 
			'TBDL': 'MS', 
			'FBCCP': 'MS', 
			'Plank': 'Push', 
			'OCPr': 'Push', 
			'UBPlyo': 'Push', 
			'OCPull': 'Pull', 
			'PP': 'Pull', 
			'TGULC': 'ST', 
			'FRCX': 'ST', 
			'OCCC': 'ST', 
			'PhCr': 'C', 
			'Gly': 'C', 
			'Endur': 'C'}

class Movement:
	def __init__(self,id,name,mtype):
		self.id = id
		self.name = name
		self.mtype = mtype
		self.assess = []
		self.parent = None
		self.kids = []

	def __str__(self):
		return '%s' % (self.name)
		
	
ReqMove1 = ['LS','MS','ST']
NTrainPerWeek = 3
NWeek = 8

CardioWeekPattern1 = ['PhCr','PhCr','PhCr','Gly','Gly','Gly','Endur']
CardioWeekPattern = ['Endur','PhCr','Endur','Gly','Endur','PhCr','Endur']

assert len(CardioWeekPattern) == NWeek-1, 'CardioWeekPattern != NWeek?!'

AssessWeek = 8

def enumSessions(randMove1):	
	# random.shuffle(randMove1)
	
	# ReqMove1 -> [ [a1,a2,b1,b2,c] ]
	sessions = { a1: [] for a1 in randMove1 }
	
	for i,a1 in enumerate(randMove1):
		wo = [ MoveTbl[a1] ]
		a2seq = A2Seq[a1]
		
		for a2 in a2seq:
			
			wo2 = wo[:]
			wo2.append( MoveTbl[a2] )
			nonA12 = Move1.keys()
			nonA12.remove(a1)
			nonA12.remove(a2)
			nonA12.remove('C') # Cardio is special
			
			for mo in nonA12:
				for b1 in MoveTbl[mo].kids:
					wo3 = wo2[:]
					wo3.append(b1)
				
					for mo2 in nonA12:
						if mo2 == mo:
							continue
						
						for b2 in MoveTbl[mo2].kids:
							wo4 = wo3[:]
							wo4.append(b2)
							
							# Cardio is special
							for c in MoveTbl['C'].kids:
								wo5 = wo4[:]
								wo5.append(c)
								
								sessions[a1].append(wo5)

		print 'enumSession %d: A1=%s NAlternatives=%d' % (i,MoveTbl[a1].name,len(sessions[a1]))
	return sessions

def rptAllSessions(sessions,outf):
	
	outs = open(outf,'w')
	outs.write('I,A2,B1,EG1,B2,EG2,C\n')

	for i,a1 in enumerate(randMove1):
		logLine = '%d: A1=%s NAlternatives=%d' % (i,MoveTbl[a1].name,len(sessions[a1]))
		outs.write('\n# %s\n' % logLine )
		for j,wo in enumerate(sessions[a1]):
			a1,a2,b1,b2,c = wo
			eg1List = [k.name for k in b1.kids]
			eg1 = '; '.join( eg1List )
			eg2 = '; '.join( [k.name for k in b2.kids] )
			outs.write('%d,"%s","%s","%s","%s","%s","%s"\n' \
					% (j+1,a2.name,b1.name,eg1,b2.name,eg2,c.name) )
			
	outs.close()
	print 'rptAllSessions: allSesssions written to',outf

def bldWOSched():
	
	woSched = {} # week -> day -> woList
	for wi in range(NWeek):
		woSched[wi] = {}
		
		weekCardio = ( 'Assess' if wi==AssessWeek-1 else MoveTbl[CardioWeekPattern[wi] ] )
		
		for si in range(NTrainPerWeek):
			if wi==AssessWeek-1:
				woSched[wi][si] = ['Assess']
				continue
				
			a1id = randMove1[si]
			a1 = MoveTbl[a1id] 
			a2seq = A2Seq[a1id]
			
			for a2id in a2seq:
				a2 = MoveTbl[a2id] 
				nonA12 = Move1.keys()
				nonA12.remove(a1id)
				nonA12.remove(a2id)
				nonA12.remove('C') # Cardio is special
				
				mo1,mo2 = random.sample(nonA12,2)
				b1 = b2 = e1 = e2 = None
				
				b1 = random.choice(MoveTbl[mo1].kids)
				b2 = random.choice(MoveTbl[mo2].kids)
				
				# e1 = random.choice(b1.kids)
				# e2 = random.choice(b2.kids)
				# woSched[wi][si] = [e1.name,e2.name,weekCardio]
				
				woSched[wi][si] = [a1.name,b1.name, a2.name,b2.name,weekCardio.name]
		
	return woSched

WOSchedTemplate = """
<html>
<head>
<title>{{ title }}</title>
</head>
<body>

<table border=2>
<TR>
  <TH class="c0">Week#</TH>
  <TH class="c0">Mon</TH>
  <TH class="c0">Wed</TH>
  <TH class="c0">Fri</TH>
 </TR>
{% for week in weekList %}
<TR>
	<TD class="c0">{{loop.index}}</TD>
	<TD class="c0">{{week['0']}}</TD>
	<TD class="c0">{{week['1']}}</TD>
	<TD class="c0">{{week['2']}}</TD>
</TR>
{% endfor %}
</table>

</body>
</html>
"""

def rptWOSched(woSched,outf):
	
	weekList = []
	for wi in range(NWeek):
		wdict = {}
		for si in range(NTrainPerWeek):
			elist = woSched[wi][si]
			wdict[str(si)] = '<br>'.join(elist)
		weekList.append(wdict)
		
	template = jinja2.Template(WOSchedTemplate)
	result = template.render(title='Workout Schedule', weekList=weekList)

	outs = open(outf,'w')
	outs.write(result)
	outs.close()

	print 'rptWOSched: WOSched written to',outf
	
if __name__ == '__main__':
	MoveTbl = {}
	
	for id,name in Move1.items():
		m = Movement(id,name,1)
		m.parent = None
		MoveTbl[id] = m
		
	for move1,assList in Assess1.items():
		m = MoveTbl[move1]
		m.assess = assList
		
	for m2id,m1id in Move2to1.items():
		name2 = Move2[m2id]
		m2 = Movement(m2id,name2,2)
		m2.parent = MoveTbl[m1id]
		MoveTbl[m1id].kids.append(m2)
		MoveTbl[m2id] = m2
		
	FADir = '/Users/rik/Personal/kidsWork/fitnessAlchemist/'
	egFile = FADir + 'pgExamples.csv'
	reader = csv.DictReader(open(egFile))
	for i,entry in enumerate(reader):
		# Move2,EgIdx,ExampleName
		idx = int(entry['EgIdx'])
		name3 = entry['ExampleName']
		m3 = Movement(idx,name3,3)
		m2 = MoveTbl[entry['Move2']]
		m2.kids.append(m3)
		m3.parent = m2
			
	randMove1 = ReqMove1[:]
	sessions = enumSessions(randMove1)
	
	allSessionsFile = FADir + 'workoutAlternatives.csv'
	rptAllSessions(sessions,allSessionsFile)
	
	nrand = 10
	for ir in range(nrand):
		woSched = bldWOSched()
		
		woSchedFile = FADir + 'woSched-%d.html' % (ir)
		rptWOSched(woSched, woSchedFile)
	
	
	
	
		
	