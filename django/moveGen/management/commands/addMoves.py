'''addMoves: moveGen mgmt command to add new movements
Created on Mar 16, 2018

@author: rik
'''

from collections import defaultdict
import csv 

from django.core.management.base import BaseCommand

from moveGen.models import Movement

Tasks = ['Leg Strength', 'Max Strength', 'Stabilize', 'Push', 'Pull', 'Cardio']

def loadNewMoves(inf):
	rdr = csv.reader(open(inf))
	currTask = currAssmt = currAccry = None
	
	addList = [] # (line,level,parent,child)
	
	for ir,row in enumerate(rdr):
		if ir==0: continue 
		# drop header but ASSUME it is:
		# Task,Assess,Access,Examples+
		# Primary Movt Tasks,Assessment,Accessory Mov'ts,Examples,,,
		
		for fi,fld in enumerate(row):
			if fi==0 and fld != '':
				currTask = fld.strip()
				add = (ir,'Task',None,currTask)
				addList.append(add)
			if fi==1 and fld != '':
				currAssmt = fld.strip()
				add = (ir,'Measure',currTask,currAssmt)
				addList.append(add)
			if fi==2 and fld != '':
				currAccry = fld.strip()
				add = (ir,'Accessory',currAssmt,currAccry)
				addList.append(add)
			
			if fi>2 and fld != '':
				add = (ir,'Exercise',currAccry,fld.strip())
				addList.append(add)
				
	print('loadNewMoves: NAdds=%d' % (len(addList)))
	return addList

class Command(BaseCommand):
	help = 'moveGen command to add new moves, assessments, accessories, examples'
	
	def add_arguments(self, parser):
		parser.add_argument('startDate', nargs='?', default='noStartSpecified') 

	def handle(self, *args, **options):

		dataDir = '/Data/whbFit/fitAlchem/'
		moveFile = dataDir + 'TFA_ProgramMap_180315.csv'
		addList = loadNewMoves(moveFile)
		addTypeTbl = defaultdict(list)
		for add in addList:
			line,level,parent,child = add
			addTypeTbl[level].append(add)
		for k in addTypeTbl.keys():
			print (k,len(addTypeTbl[k]))

		nfnd=0
		newMoveTbl = defaultdict(list)
		for add in addList:
			line,level,parent,child = add
			if level=='Task' and child in Tasks:
				nfnd += 1
				continue
			
			# qs = Movement.objects.filter(name__iexact=child)
			# allowing case-insensitive doesn't help
			qs = Movement.objects.filter(name=child)
			fnd = list(qs)
			if len(fnd)==0:
				# NB: make new names qualified on level (cf. Leg Strength)
				newMoveTbl[(child,level)].append(add)
			elif len(fnd)==1:
				moveObj = fnd[0]
				if moveObj.mtype == level:
					nfnd += 1
				else:
					print('%s %s idx=%s mtype=%s' % (child, level, moveObj.idx, moveObj.mtype))
			else:
				print('addMoves: multiple moves?!',len(fnd),add)
		
		print('addMoves: NFnd=%d NNew=%d\n' % (nfnd,len(newMoveTbl)))	
		print('Name,NType,NRef,Refs')	
		for k in newMoveTbl.keys():
			(newmove,nmlev) = k
			refs = [(add[0],add[2]) for add in newMoveTbl[k]]
			add = newMoveTbl[k][0]
			line,level,parent,child = add
			print('"%s",%s,%d,"%s"' % (newmove,nmlev,len(refs),refs))

			
		
if __name__ == '__main__':
	cmd = Command()
	cmd.handle()