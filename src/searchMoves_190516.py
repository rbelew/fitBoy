''' searchMoves: support search for subsets of movements with particular features

Created on Mar 10, 2019

@author: rik
'''

from collections import defaultdict
import csv
import sys

NETask = 0
NJoint = 0
AllJointTbl = {}
NContract = 0
NMoveType = 0
AllJointPlanes = {}
UnilateralJoints = {'hip': ['internal/external rotation'],
					'spine':['rotation','lateral flexion']}

## util


def freqHist3(tbl):
	"Assuming values are frequencies, returns UNSORTED?! list of (val,freq) items in descending freq order"
	def cmpd1(a,b):
		"decreasing order of frequencies"
		# return cmp(b[1], a[1])
		x = b[1]
		y = a[1]
		return (x > y) - (x < y)

	
	flist = list(tbl.items())
	# flist.sort(flist, cmpd1)
	return flist

## eo-util

def loadExer(inf):

	global NETask
	global NJoint
	global AllJointTbl
	global NContract
	global NMoveType
	global AllMoveTypes

	exerTbl = defaultdict(list)
	etaskTbl = defaultdict(list)
	jointTbl = defaultdict(list)
	contractTbl = defaultdict(list)
	moveTypeTbl = defaultdict(list)
	
	reader = csv.DictReader(open(inf))
	
	allFldNames = ['idx','name','abbrev','mtype','moveTask','cardio','parent_id','etask','unilateralP','joint','movtType','contractType','issues']
	simpleFldNames = ['name','abbrev','mtype','moveTask','cardio','etask','issues']
	print('# Dropped exercisesIdx,Dropped exercise,Issue')
	for i,entry in enumerate(reader):
		exer = {}
		idx = int(entry['idx'])
		if entry['issues'].strip() != '':
			print('%d,%s,%s' % (idx,entry['name'],entry['issues']))
			continue
		
		exer['idx'] = idx
		if entry['parent_id'].strip() == '':
			pidx = -1
		else:
			pidx =  int(entry['parent_id'])
			
		exer['pidx'] = pidx
		for fn in simpleFldNames:
			exer[fn] = entry[fn]
			
		if entry['unilateralP'] == 'TRUE':
			exer['unilateralP'] = True
		else:
			exer['unilateralP'] = False

		tlist = []
		for ts in entry['etask'].split(','):
			t = ts.strip().lower()
			if t != '':
				etaskTbl[t].append(idx)
				tlist.append(t)
		exer['etask'] = tlist
			
		jlist = []
		#UNIMPLEMENTED:  only CLUSTER exercises might have "all" joints mentioned in future- 190426
		for js in entry['joint'].split(','):
			j = js.strip().lower()
			if j != '':					
				jointTbl[j].append(idx)
				jlist.append(j)
		exer['joint'] = jlist
			
		moveStrList = []
		if  entry['movtType'] == 'all':
			# NB: can only flag here, AllJointPlanes not yet available; substitute in exerFactors()
			moveStrList = ['all']
		else:
			moveStrList = entry['movtType'].split(',')
			
		mlist = []
		for ms in moveStrList:
			m = ms.strip().lower()
			if m != '':
				moveTypeTbl[m].append(idx)
				mlist.append(m)
					
		exer['movtType'] = mlist

		clist = []
		for cs in entry['contractType'].split(','):
			c = cs.strip().lower()
			if c != '':
				contractTbl[c].append(idx)
				clist.append(c)
		exer['contractTypes'] = clist
			
		exerTbl[idx] = exer

	NETask = len(etaskTbl)
	NJoint = len(jointTbl)
	AllJointTbl = jointTbl.copy()
	NContract = len(contractTbl)
	NMoveType = len(moveTypeTbl)
		
	print('\n# loadExer: NExer=%d NETask=%d NJoint=%d NContract=%d NMove=%d' % \
			(len(exerTbl),NETask,NJoint,NContract,NMoveType))
	return exerTbl,jointTbl,contractTbl,moveTypeTbl

def loadTskJnt2pln(inf):
	'''also collect AllJointPlanes
	'''
	tj2pTbl = {} # (t,j) -> [plane]
	global AllJointPlanes
	AllJointPlanes = defaultdict(set)
	reader = csv.DictReader(open(inf))
	for i,entry in enumerate(reader):
		t = entry['task'].strip().lower()
		j = entry['joint'].strip().lower()
		k = (t,j)
		planeStrList = entry['plane'].split(',')
		plist = []
		for p in planeStrList:
			p2 = p.strip().lower()
			plist.append(p2)
			AllJointPlanes[j].add(p2)
		tj2pTbl[k] = plist
		
	for j,planeList in UnilateralJoints.items():
		for p in planeList:
			AllJointPlanes[j].add(p)
			
	# 190515: HACK to add wrist prior to its being used!
	AllJointPlanes['wrist'] = {'flexion/extension', 'abd/adduction'}
			
	print('loadTskJnt2pln: AllJointPlanes')
	allJnt = list(AllJointPlanes.keys())
	allJnt.sort()
	for j in allJnt:
		print('%s:\t%s' % (j,AllJointPlanes[j]))
		
	return tj2pTbl
	
def diceSim(s1,s2):
	if len(s1)+len(s2) == 0:
		return 0.
	
	shared = s1.intersection(s2)
	return float(len(shared))/(len(s1)+len(s2))

def normSim(s1,s2,denom):
	if len(s1)+len(s2) == 0:
		return 0.
	
	shared = s1.intersection(s2)
	return float(len(shared))/denom

def getJointPlanes(ex):
	'''return {joint:planeList} for all exercise's joints'''

	taskList = ex['etask']	
	jset = set(ex['joint'])
	mtype = ex['movtType']
	ulat = ex['unilateralP']
	
	jpset = set()
	if taskList[0]=='body control':

		# 	"if there is info in this [MoveType] column, that info should be translated
		# 	  into the appropriate joint column (previously tagged on Body
		# 	  Control movt's) as planer information (i.e. internal rotation
		# 	  gets translated into internal/external rotation plane)"

		for j in jset:
			if mtype == ['all']:
				planeList = AllJointPlanes[j]
			else:
				planeList = mtype
			for p in planeList:
				jpset.add( (j,p) )	

	# for all eTask other than BodyControl, refer to  tj2pTbl
	else:
		# NB: only non-BodyControl can be ulat
		# NB: ulat flag may imply new JOINTS
		if ulat:
			for uj,planeList in UnilateralJoints.items():
				jset.add(uj)
				for p in planeList:
						jpset.add(( uj,p) )

		# 2do: hassle to go thru ALL TskJnt2PlnTbl.keys; build task index
		for task in taskList:
			for k in TskJnt2PlnTbl.keys():
				t,j = k 
				if t!=task:
					continue
				for p in TskJnt2PlnTbl[k]:
					jpset.add( (j,p) )
			
	return jpset
	
def exerFactors(ex1,ex2,verbose=False):
	''' v2: use TaskJoint2plane table
	return [jsim,planeSim,contractSim]
	'''

	global TskJnt2PlnTbl	
	
	tset1 = set(ex1['etask'])
	tset2 = set(ex2['etask'])
	tsim = normSim(tset1,tset2,NETask)
	
	j1 = ex1['joint']
	j2 = ex2['joint']

	jset1 = set(j1)
	jset2 = set(j1)
	jsim = normSim(jset1,jset2,NJoint)
	
	m1 = ex1['movtType']
	m2 = ex2['movtType']

	u1 = ex1['unilateralP']
	u2 = ex2['unilateralP']
	
	# pairDirection: capture a/symmetry of etask priority
# 	if t1=='Body Control' and t2 !='Body Control':
# 		pairDirection = [0,1]
# 	elif t1!='Body Control' and t2 =='Body Control':
# 		pairDirection = [1,0]
# 	elif t1=='Body Control' and t2 =='Body Control':
# 		pairDirection = [0,0]
# 	else:
# 		pairDirection = [1,1]

	cset1 = set(ex1['contractTypes'])
	cset2 = set(ex2['contractTypes'])
	csim = normSim(cset1,cset2,NContract)

	## NB: no reason to compare joint+moveType pair overlap if no joint overlap!
	if jset1.intersection(jset2) == set():
# 		print('%d %s "%s" %d %s "%s": no overlapping joints' % \
# 			(ex1['idx'],ex1['name'],j1,ex2['idx'],ex2['name'],j2))	
		if verbose:
			print('%03d %50s "%s"\n%03d %50s "%s"\n\tjsim=0.0! planeSim=%f csim=%f' % \
				(ex1['idx'],ex1['name'],[],ex2['idx'],ex2['name'],[],0.0,csim))
			
		return [0., 0., csim]
	
	jpset1 = set(getJointPlanes(ex1))
	jpset2 = set(getJointPlanes(ex2))
			
	planeSim = diceSim(jpset1,jpset2)

	return [tsim,jsim, planeSim,csim]

def exerSim(ex1,ex2,verbose=False):
	
	[tsim,jsim,psim,csim] = 	exerFactors(ex1,ex2,verbose)
	
	tsim = 0.2
	jwgt = 0.3
	pwgt = 0.5
	cwgt = 0.0
	
	sim = jwgt * jsim + psim * pwgt + cwgt * csim 
	return sim


def rptGraph(exerTbl,outf,verbose=False):	
	outs = open(outf,'w')
	outs.write('Source;Target;Weight\n')
	allEIdx = list(exerTbl.keys())
	allEIdx.sort()
	nmatch = 0
	nzero = 0
	etaskWgt = 1.0
	
	for eidx1 in allEIdx:
		nonzFnd = False
		for eidx2 in allEIdx:
			if eidx2 <= eidx1:
				continue
			ex1 = exerTbl[eidx1]
			ex2 = exerTbl[eidx2]
			sim = exerSim(ex1,ex2,verbose)
			if sim > 0.:
				outs.write('%s;%s;%f\n' % (ex1['name'],ex2['name'],sim))
				nmatch += 1
			else:
				nzero += 1
				continue
			# add etask links
			nonzFnd = True
		if nonzFnd:
			for etask in ex1['etask']:
				outs.write('%s;%s;%f\n' % ('* '+etask,ex1['name'],etaskWgt))
	outs.close()
	print('# rptGraph: NMatch=%d NZeroSim=%d' % (nmatch,nzero))

def rptFactors(exerTbl,outf):	
	outs = open(outf,'w')
	outs.write('Source,Target,TaskSim,JointSim,PlaneSim,ContractSim,Sim\n')
	allEIdx = list(exerTbl.keys())
	allEIdx.sort()
	nmatch = 0
	nzero = 0
	
	for eidx1 in allEIdx:
		for eidx2 in allEIdx:
			if eidx2 <= eidx1:
				continue
			ex1 = exerTbl[eidx1]
			ex2 = exerTbl[eidx2]
			factors = exerFactors(ex1,ex2)
			factorStr = [str(f) for f in factors]
			sim = exerSim(ex1,ex2)
			fldList = [ex1['name'],ex2['name']] + factorStr + [str(sim)]
			if sim > 0.:
				flds = ','.join(fldList)
				outs.write('%s\n' % (flds))
				nmatch += 1
			else:
				nzero += 1
				continue
	outs.close()

def rptExerJoint(exerTbl,outf):	
		
	allEIdx = list(exerTbl.keys())
	allEIdx.sort()
	nmatch = 0
	nzero = 0
	
	allJnt = list(AllJointTbl.keys())
	allJnt.sort()
	
	outs = open(outf,'w')
	jHdr = ','.join(allJnt)
	outs.write('Idx,Name,ETask,Unilat,Joints,'+jHdr+'\n')
	
	for eidx in allEIdx:
		ex = exerTbl[eidx]
		jpSet = frozenset(getJointPlanes(ex))
		j2pTbl = defaultdict(list)
		for j,p in jpSet:
			j2pTbl[j].append(p)
		jinfoList = []
		for j in allJnt:
			if j in j2pTbl:
				jinfoList.append(j2pTbl[j])
			else:
				jinfoList.append([])
			
		taskStr = ';'.join(['%s' % (t) for t in ex['etask']	]) 
		jntList = ex['joint']
		jntList.sort()
		jlistStr = ','.join(jntList)
		
		# NB: double quote all plane lists individually
		qStrList = []
		for plist in jinfoList:
			if len(plist)>0:
				plist.sort()
				qStrList.append('"%s"' % ','.join(plist))
			else:
				qStrList.append(' ')

		jstr = ','.join(qStrList)
		outs.write('%s,%s,"%s",%s,"%s",%s\n' % (ex['idx'], ex['name'], taskStr, ex['unilateralP'],jlistStr, jstr))
				
	outs.close()

def rptIdentJP(exerTbl,outf):
	allEIdx = list(exerTbl.keys())
	allEIdx.sort()

	jpCompTbl = defaultdict(list)
	
	for eidx in allEIdx:
		ex = exerTbl[eidx]
		jpSet = frozenset(getJointPlanes(ex))
		jpCompTbl[jpSet].append(ex['idx'])
	
	outs = open(outf,'w')
	outs.write('JPSetIdx,JPSetSize,JPSet,CanonE,EIdx,EName,JPVariants,Tags\n')
	for i,jpSet in enumerate(jpCompTbl.keys()):
		if len(jpCompTbl[jpSet]) == 1:
			continue
		for k,eidx in enumerate(jpCompTbl[jpSet]):
			ex = exerTbl[eidx]
			canon = '*' if k==0 else ' '
			jpList = list(jpSet)
			jpList.sort()
			jpStr = ';'.join(['%s+%s' % (j,p) for j,p in jpList])
			outs.write('%d,%d,"%s",%s,%d,%s\n' % (i+1,len(jpSet),jpStr,canon,eidx,ex['name']))
	outs.close()

	
if __name__ == '__main__':
	
	dataDir = '/Data/whbFit/TFApp/'
	moveFile = dataDir + 'TaggedMoves_190515.csv'

	global TskJnt2PlnTbl
	tskJnt2plnFile = dataDir + 'funcMoveXjoint2plane_190512.csv'
	TskJnt2PlnTbl = loadTskJnt2pln(tskJnt2plnFile)

	exerTbl,jointTbl,contractTbl,moveTypeTbl = loadExer(moveFile)
	
	verbose = True
	
	outf = dataDir + 'exerJointPlanes.csv'
	rptExerJoint(exerTbl,outf)
		
	outf = dataDir + 'exerSim.csv'
	if verbose:
		print('# VERBOSE similarities')		
	rptGraph(exerTbl,outf,verbose=verbose)
				
	outf = dataDir + 'exerFactors.csv'
	rptFactors(exerTbl,outf)
	
	outf = dataDir + 'identJP.csv'
	rptIdentJP(exerTbl,outf)

	