
from django.views.generic.edit import DeleteView

from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, loader
from django.shortcuts import get_object_or_404, render
# django 2.0
# from django.core.urlresolvers import reverse
from django.urls import reverse

from django.contrib.auth.decorators import login_required
from django.db.models.lookups import IExact
from django.db import transaction
from django.db import IntegrityError
from django.urls import reverse_lazy

from .models import *
from .forms import *

from collections import defaultdict
import copy 
from datetime import datetime
import json
import math
import random
import string

import logging
logger = logging.getLogger(__name__)

MoveOrder = ['A1','B1','A2','B2','C','B3']

MeasureColor = {"Assault Bike": [255, 153, 51], 
					"Split Squat": [255,0,0],
					"TB Deadlift": [236,236,19], # [255,255,0],
					"Pull-Up": [164,194,244],
					"Push-Up": [153,204,0], # [182,215,168],
					"Turkish Get-Up" : [180,167,214],
					"OPEN": [230,230,230],
					"Hip CAR": [255, 102, 204]}; 

# OnlyMesoMentions = True ==> 
# restrict A2 selection to those Measures mentioned elsewhere in Meso; cf bldTestNMWOS()

# OnlyMesoMentions = False ==> use *all* Measures
OnlyMesoMentions = False  
MinNQual = 4

def rgbColorStr(rgbTuple):
	return 'rgb(%d,%d,%d)' % tuple(rgbTuple)

def index(request):
	return render(request, 'moveGen/index.html')

def need2login(request):
	return render(request, 'moveGen/need2login.html', {})

@login_required
def bldMesoSys(request):
	'''Create and specify SYSTEMS of movements
		Use these to create cohort and indiv MESO schedules
	'''
				
	sysqs = MesoSystem.objects.all()
	sysList = list(sysqs)
	
	context = {'sysList': sysList}
	
	return render(request, 'moveGen/bldMesoSys.html', context)

NCommitInsert = 0
NCommitUpdate = 0
@login_required
	
@login_required
def cloneMesoSys(request,mesoSysPK):

	ms = MesoSystem.objects.get(idx=mesoSysPK)
	
	# NB: DEEP copy required on recursive moveDict
	dictClone = copy.deepcopy(ms.moveDict)
	
	newMS = MesoSystem()
	# 180719 HACK
	# newMS.name= ms.name+' (clone)'
	pname = ms.name[:10]
	newMS.name = pname+'...CLONE'
	newMS.author = request.user
	newMS.moveDict = dictClone
	newMS.save()

	sysqs = MesoSystem.objects.all()
	sysList = list(sysqs)
	
	context = {'sysList': sysList}
	
	return render(request, 'moveGen/bldMesoSys.html', context)
	
@login_required
def deleteMesoSys(request,mesoSysPK):
	
	ms = MesoSystem.objects.get(idx=mesoSysPK)
	ms.delete()

	sysqs = MesoSystem.objects.all()
	sysList = list(sysqs)
	
	context = {'sysList': sysList}
	
	return render(request, 'moveGen/bldMesoSys.html', context)
	
CurrMoveList = []
def moveDict2list(moveDict):
	'''convert MesoSystem.mdict to simple list of Movement objects
	'''
	
	global CurrMoveList
	CurrMoveList = []
	
	def traverse(nd):
		global CurrMoveList
		mo = Movement.objects.get(pk=nd['idx'])
		CurrMoveList.append(mo)
		for k in nd['children']:
			traverse(k)
			
	topKids = moveDict['children']
	for k in topKids:
		traverse(k)
		
	CurrMoveList.sort(key=lambda mo: mo.idx)
	
	return CurrMoveList
		
@login_required
def createCohortMeso(request,mesoSysPK):
	'''use MesoSys specification of qualities inclusion
		allow exclusion of accessories
	'''
	
	ms = MesoSystem.objects.get(pk=mesoSysPK)
	if not ms.movesCommited:
		errMsg = 'createCohortMeso: %s MesoSystem Movements not committed?!' % (mesoSysPK)
		return render(request, 'moveGen/err.html', {'errMsg': errMsg, 'except': '(no exception)'})
	
	moveDict = ms.moveDict
	moveList = moveDict2list(moveDict)
					
	measureList = [mo for mo in moveList if mo.mtype == 'Measure']

	# Need to create table of ALL accessories, so client can display any possible
	#  accryTbl: measure.idx -> ['accryIdx_accessName', ...]
	
	accryTbl = defaultdict(list)
	
	accryList = [mo for mo in moveList if mo.mtype == 'Accessory']
	
	unMentionedParents = set(measureList)
	
	for accry in accryList:
		ameas = accry.parent
		if ameas in measureList and ameas in unMentionedParents:
			unMentionedParents.remove(ameas)

		lbl = '%s_%s' % (accry.idx,accry.name)
		measureIdx = ameas.idx
		accryTbl[measureIdx].append(lbl)
	accryTblJSON = json.dumps(accryTbl)
	
	for mo in unMentionedParents:
		infoStr = 'createCohortMeso: MesoSys %s %s No accessories for Measure %s [%s]; dropped!' % \
				(ms.idx,ms.name, mo.name, mo.idx)
		print(infoStr)
		logger.info(infoStr)
		measureList.remove(mo)
		
	measureList.sort(key=lambda mo: mo.name)

	infoStr = 'createCohortMeso: Using MesoSys %s %s NMoves=%d' % (ms.idx,ms.name,len(moveList))
	print(infoStr)
	logger.info(infoStr)
		
	context = {}
	context['mesoSysIdx'] =  ms.idx
	context['mesoSysName'] =  ms.name
	context['measureList'] =  measureList
	context['accryTbl'] =  accryTblJSON
	
	return render(request, 'moveGen/createCohortMeso.html', context)

@login_required
def createIndivMeso(request,mesoSysPK):
	'''use MesoSys specification of qualities inclusion
		allow exclusion of accessories
	'''
			
	ms = MesoSystem.objects.get(pk=mesoSysPK)
	if not ms.movesCommited:
		errMsg = 'createIndivMeso: %s MesoSystem Movements not committed?!' % (mesoSysPK)
		return render(request, 'moveGen/err.html', {'errMsg': errMsg, 'except': '(no exception)'})
	
	moveDict = ms.moveDict
	moveList = moveDict2list(moveDict)

	measureList = [mo for mo in moveList if mo.mtype == 'Measure']

	# Need to create table of ALL accessories, so client can display any possible
	#  accryTbl: measure.idx -> ['accryIdx_accessName', ...]
	
	accryTbl = defaultdict(list)
	
	accryList = [mo for mo in moveList if mo.mtype == 'Accessory']

	unMentionedParents = set(measureList)
	
	for accry in accryList:
		ameas = accry.parent
		if ameas in measureList and ameas in unMentionedParents:
			unMentionedParents.remove(ameas)

		lbl = '%s_%s' % (accry.idx,accry.name)
		measureIdx = ameas.idx
		accryTbl[measureIdx].append(lbl)
	accryTblJSON = json.dumps(accryTbl)

	for mo in unMentionedParents:
		infoStr = 'createIndivMeso: MesoSys %s %s No accessories for Measure %s [%s]; dropped!' % \
				(ms.idx,ms.name, mo.name, mo.idx)
		print(infoStr)
		logger.info(infoStr)
		measureList.remove(mo)
	
	measureList.sort(key=lambda mo: mo.name)

	infoStr = 'createIndivMeso: Using MesoSys %s %s NMoves=%d' % (ms.idx,ms.name,len(moveList))
	print(infoStr)
	logger.info(infoStr)

	context = {}
	context['mesoSysIdx'] =  ms.idx
	context['mesoSysName'] =  ms.name
	context['measureList'] =  measureList
	context['accryTbl'] =  accryTblJSON
	
	return render(request, 'moveGen/createIndivMeso.html', context)

@login_required
def saveMeso(request):
	
	meso2 = MesoCycle2()

	meso2.author = request.user
	meso2.name = request.POST['mesoName'] 
	desc = request.POST['mesoDesc'].strip()
	
	meso2.desc =  " " if len(desc) == 0 else desc
	
	# cdate is auto_now_add
	meso2.audience = request.POST['mesoAudience'] 

	mesoSysIdx = request.POST['mesoSysIdx'] 
	meso2.system = MesoSystem.objects.get(pk=mesoSysIdx)

	# 2do ASAP: make these variable  automatically change svg grid
	if meso2.audience == 'cohort':		
# 		meso2.coh_nweek = int(request.POST['coh_nweek'])
# 		meso2.coh_nsessionWeek = int(request.POST['coh_nsessionWeek'])
		meso2.nweek = 8
		meso2.nsessionWeek = 3

		nsession=meso2.nsessionWeek
		moveWid=300
		moveHgt=60
		
	elif meso2.audience == 'indiv':
		# meso2.totSession = int(request.POST['totSession'])
		meso2.totSession = 10

		meso2.nweek=1
		nsession=meso2.totSession
		moveWid=100
		moveHgt=60


	moveSeqDetailStr = request.POST['moveSeq'] 
	moveSeqDetail = json.loads(moveSeqDetailStr)

	# replace move dicts with just move's idx
	# {'idx': '121', 'name': 'Assault Bike', 'sortOrder': '0', 'x': 0, 'y': 0}
	# NB: make moveSeq have int indices
	moveSeq = {}
	moveSeqNames = {}
	for wis in moveSeqDetail.keys():
		wi = int(wis)
		moveSeq[wi] = {}
		moveSeqNames[wi] = {}
		for sis in moveSeqDetail[wis].keys():
			si = int(sis)
			a1dict = moveSeqDetail[wis][sis][0]
			a1idx = int(a1dict['idx'])
			a1task = a1dict['task']
			
			a2dict = moveSeqDetail[wis][sis][1]
			if a2dict=='OPEN':
				a2val = a2task = 'OPEN'
			else:
				a2idx = int(a2dict['idx'])
				a2task = a2dict['task']
				a2val = a2idx
			moveSeq[wi][si] = [a1idx,a2val]
			moveSeqNames[wi][si] = [a1task,a2task]
	meso2.moveSeq = moveSeq
	
	# includeQual: list of those included
	includeQualStr = request.POST['includeQual'] 
	includeQual = json.loads(includeQualStr)
	includQualIdxList = []
	for qualLbl in includeQual:
		qualIdx = qualLbl.split('_')[1]
		includQualIdxList.append(qualIdx)
		
	if len(includQualIdxList) < MinNQual:
		errMsg = 'saveMeso: %s  not saved, only %d included qualities' % (meso2.name,len(includQualIdxList))
		return render(request, 'moveGen/err.html', {'errMsg': errMsg, 'except': '(no exception)'})

	meso2.includeQual = includQualIdxList
		
	# includeQual: list of those included
	excludeAccryStr = request.POST['excludeAccry'] 
	excludeAccry = json.loads(excludeAccryStr)
	excludeAccryList = []
	for accryLbl in excludeAccry:
		accryIdx = int(accryLbl.split('_')[0])
		excludeAccryList.append(accryIdx)
	meso2.excludeAccry = excludeAccryList
	
	meso2.save()

	form = NameSchedForm()

	moveSeqNamesStr = json.dumps(moveSeqNames)	
					
	context = {'meso2': meso2,
				'form': form,
				'moveWid': moveWid,
				'moveHgt': moveHgt,
				'nsession': nsession,
				'moveSeqStr': moveSeqNamesStr,
				'includeQual': includeQualStr,
				'excludeAccry': excludeAccryStr
				}

	return HttpResponseRedirect('/moveGen/pprintMeso/%d/' % (meso2.pk) )
	# return render(request, 'moveGen/pprintMeso.html',context )

@login_required
def selectMeso(request):

	# import pdb; pdb.set_trace()
	if request.method == 'POST':
		qform = PickMeso(request.POST)
		if qform.is_valid():
			qryData = qform.cleaned_data
			qurl = '/moveGen/bldSched/%s/' % (qryData['mesoName']) 
			return HttpResponseRedirect(qurl)
	else:
		qform = PickMeso()
		
	return render(request, 'moveGen/selectMeso.html', {'form': qform})

def pprintMoveSeq(moveSeq):
	'''convert Move -> MoveList to description list
	'''
	allMove = list(moveSeq.keys())
	allMove.sort()
	descStr = ''
	for k in allMove:
		descStr += '\t<DT>%s</DT><DD>%s</DT>\n' % (k,moveSeq[k])
	descStr = '<DL>\n' + descStr + '</DL>\n'
	return descStr

	
@login_required
def pprintMeso(request,meso2PK):
	try:
		meso2 = MesoCycle2.objects.get(pk=meso2PK)
	except Exception as e:
		print('pprintMeso: bad meso2 PK %s ?!' % (meso2PK) )
		return render(request,'moveGen/err.html', {'errMsg': 'bad meso2 PK',
													'except': e})

	# If this is a POST request then process the Form data
	if request.method == 'POST':

		# Create a form instance and populate it with data from the request (binding):
		form = NameSchedForm(request.POST)

		# Check if the form is valid:
		if form.is_valid():
			# process the data in form.cleaned_data as required (here we just write it to the model due_back field)
			schedName = form.cleaned_data['schedName']

			# redirect to a new URL:
			return HttpResponseRedirect('/moveGen/bldNMWOS/%s/%s/' % (meso2PK,schedName) )

	# If this is a GET (or any other method) create the default form.
	else:
	
		form = NameSchedForm()

		# 2do ASAP: make these variable  automatically change svg grid
		if meso2.audience == 'cohort':		
			meso2.nweek = 8
			meso2.nsessionWeek = 3
	
			nweek=meso2.nweek
			nsession=meso2.nsessionWeek
			moveWid=300
			moveHgt=60
			
		elif meso2.audience == 'indiv':
			meso2.totSession = 10
	
			nweek=1
			nsession=meso2.totSession
			moveWid=100
			moveHgt=60
			
		moveSeq = meso2.moveSeq
		moveSeqInfo = {}
		# replace move pk's with names + idx dict
		for wi in moveSeq.keys():
			moveSeqInfo[wi] = {}
			for si in moveSeq[wi].keys():
				a1idx = moveSeq[wi][si][0]
				a1 = Movement.objects.get(pk=a1idx)
				a1dict = {'name': a1.name, 'idx': a1idx, 'task': a1.task}
				
				a2idx = moveSeq[wi][si][1]
				if a2idx=='OPEN':
					a2dict = {'name': 'OPEN', 'idx': None, 'task': 'OPEN'}
				else:
					a2 = Movement.objects.get(pk=a2idx)
					a2dict = {'name': a2.name, 'idx': a2idx, 'task': a2.task}
					
				moveSeqInfo[wi][si] = [a1dict,a2dict]
		
		moveSeqStr = json.dumps(moveSeqInfo)
		
		includeQualNames = []
		for idx in meso2.includeQual:
			m = Movement.objects.get(pk=idx)
			includeQualNames.append(m.task)
			
		excludeAccryNames = []
		for idx in meso2.excludeAccry:
			m = Movement.objects.get(pk=idx)
			excludeAccryNames.append(m.name)
					
		context = {'meso2': meso2,
					'form': form,
					'moveWid': moveWid,
					'moveHgt': moveHgt,
					'nweek': nweek,
					'nsession': nsession,
					'moveSeqStr': moveSeqStr,
					'includeQual': includeQualNames,
					'excludeAccry': excludeAccryNames,
					}
					
		return render(request, 'moveGen/pprintMeso.html', context)

def bldTestNMWOS(meso2):
	if meso2.audience=='cohort':
		nweek = meso2.nweek
		nsessionWeek = meso2.nsessionWeek
	else:
		nweek = 1
		nsessionWeek = meso2.totSession
		
	
	# NB: moveSeq requires STRING indices, woSched uses int
	woSched = {}
	
	# 180407: "OPEN" means selected randomly from movements mentioned in moveSeq
	# NB: consider only SET, NOT according to distribution consistent with multiset allocation
	# TOGETHER WITH any other includeQual
		
	# collect all  Movement mentioned in schedule
	allMoveSet = set()

	for wi in range(nweek):
		wis = str(wi)
		for si in range(nsessionWeek):
			sis = str(si)
			a1idx = meso2.moveSeq[wis][sis][0]
			allMoveSet.add(int(a1idx))
			a2idx = meso2.moveSeq[wis][sis][1]
			if a2idx != 'OPEN':
				allMoveSet.add(int(a2idx))
		
	excludeAccry = [int(eidx) for eidx in meso2.excludeAccry]
	
	# 180407: augment scheduled movements with others to be included		
	for midx in meso2.includeQual:
		allMoveSet.add(int(midx))
		
	# print('bldTestNMWOS: allMove=%s' % (allMoveSet))
				
	for wi in range(nweek):
		# NB: moveSeq requires STRING indices
		wis = str(wi)
		woSched[wi] = {}
				
		for si in range(nsessionWeek):
			sis = str(si)
			if meso2.assessNow(wi,si):
				woSched[wi][si] = {'Assess': 'Assess'}
				continue

			a1idx = int(meso2.moveSeq[wis][sis][0])
			a1 = Movement.objects.get(pk=a1idx)
			a1name = a1.name

			a2idx = meso2.moveSeq[wis][sis][1]
			if a2idx=='OPEN':
				# pick random a2, anything but a1
				
				# 180323: "OPEN" means selected randomly from movements mentioned in moveSeq
				# according to distribution consistent with multiset allocation

				# make copy of allMoveNames, except a1idx
				a2candIdx = [aidx for aidx in allMoveSet if aidx != a1idx]
				a2idx = random.choice(a2candIdx)
				
			a2 = Movement.objects.get(pk=a2idx)
			a2name = a2.name
					
			# make copy of allMoveIdx, except a1idx, a2idx
			otherCandIdx = [aidx for aidx in allMoveSet if (aidx != a1idx and aidx != a2idx)]
			
			if len(otherCandIdx) < 2:
				print('bldTestNMWOS: cant select 2 other moves?!')
				woSched['errMsg'] = 'bldTestNMWOS: cant select 2 other moves?!'
				return woSched
			
			else:
				sampleList = random.sample(otherCandIdx,2)
				[mo1idx,mo2idx] = sampleList
				
			mo1 = Movement.objects.get(pk=mo1idx)
			mo2 = Movement.objects.get(pk=mo2idx)
			
			mo1children = list(Movement.objects.filter(parent=mo1))
			mo2children = list(Movement.objects.filter(parent=mo2))
			
			# 180407 exclude any accessories explicitly excluded in meso
			mo1kidsX = [kid for kid in mo1children if kid.idx not in excludeAccry]
			mo2kidsX = [kid for kid in mo2children if kid.idx not in excludeAccry]
			
			b1 = b2 = None
			
			b1 = random.choice(mo1kidsX)
			b2 = random.choice(mo2kidsX)
				
			woSched[wi][si] = {'A1': a1.pk,
							   'B1': b1.pk,
							   'A2': a2.pk,
							   'B2': b2.pk }
			
			infoStr = 'bldTestNMWOS: wi=%s si=%s a1=%s (%s) a2=%s (%s) mo1=%s mo2=%s' % \
				(wi,si,a1name,a1idx,a2name,a2idx,mo1idx,mo2idx)
			print(infoStr)
			logger.info(infoStr)

	return woSched

@login_required
def bldNMWOS(request,meso2PK,schedName):
	
	meso2PK = int(meso2PK)
	try:
		meso2 = MesoCycle2.objects.get(pk=meso2PK)
	except Exception as e:
		print('bldNMWOS: bad meso2 PK %s ?!' % (meso2PK) )
		return render(request,'moveGen/err.html', {'errMsg': 'bad meso name',
													'except': e})
		
	moveSeq = meso2.moveSeq
		
	ntrials = 1
	maxE = 0.
	bestSched = None
	minE = 1000. 
	
	for i in range(ntrials):
		tstSched = bldTestNMWOS(meso2)
		if 'errMsg' in tstSched:
			return render(request,'moveGen/err.html', {'errMsg': tstSched['errMsg'],'except': None})
		
		e = evalSched(tstSched)
		
		# print(i,e)
		
		if e > maxE:
			maxE = e
			bestSched = tstSched
		if e < minE:
			minE = e 
			
	infoStr = 'Meso2 %s NTrials=%d Min=%f Max=%f' % (meso2.name,ntrials,minE,maxE)
	print(infoStr)
	logger.info(infoStr)
	woSched = bestSched
	
	# Post Schedule data
	
	sched = Schedule()
	sched.name = schedName
	sched.stype = 'Primary'
	sched.primary = None
	sched.mesoVersion = 'v2'
	sched.meso2 = meso2
	sched.details = woSched
	sched.distribQual = maxE
	sched.save()
	schedIdx = sched.pk
	
	if meso2.audience == 'indiv':
		# NB: no secondary, unified schedules for indiv meso2
		return primaryNMSched(request,schedIdx)

	elif meso2.audience == 'cohort':
		sched2PK = bldNMSched2(sched.pk)
		return unifiedSched(request, schedIdx, sched2PK)

@login_required
def primaryNMSched(request,sched1pk):

	sched1pk = int(sched1pk)
	sched = Schedule.objects.get(pk=sched1pk)
	meso2 = sched.meso2
	if meso2.audience=='indiv':
		nweek = 1
		nsession = meso2.totSession
	elif meso2.audience=='cohort':
		nweek = meso2.nweek
		nsession = meso2.nsessionWeek

	sdetails = sched.details
	schedNamed = pprintSchedNames(sdetails)
	
	# create weekList and context for schedule template
		
	weekList = []
	for wi in range(nweek):
		dayList = []
		for si in range(nsession):
			elist = schedNamed[wi][si]
			elistStr = '<li>'.join(elist)
			elistHTML = '<ul><li>' + elistStr + '</ul>'
			dayList.append( elistHTML )
		weekList.append(dayList)


	sessionIdxList = [i+1 for i in range(nsession)]
	
	context = {'mesoIdx': meso2.pk,
				'mesoName': meso2.name,
				'mesoAudience': meso2.audience,
				'schedName': sched.name,
				'stype': 'Primary',
				'weekList': weekList,
				'nsession': nsession,
				'sessionHdrList': sessionIdxList,
				'sessionIdxList': sessionIdxList,
				'sched1Idx': sched1pk}
	return render(request, 'moveGen/schedule.html', context)

# choices given previous day's cardio

class SchedDelete(DeleteView):
	model = Schedule
	success_url = reverse_lazy('toc')
	

def bldNMSched2(sched1Idx):
	'''Create interstitial workouts between regular workouts of schedule
		Secondary workout: same a1 as previous day
						   new a1-b, a2-b associated with previous a1, a2
						   new a2 differing from previous a1,a2
						   new b1,b2 selected as bldWOSched, but disallowing b1 and b2 from previous day
						   
		180311: modified for Meso2;  
				ASSUME cohort; no secondary workouts generated for indiv
		180323: add b3, to replace slot from missing cardio
	'''

	sched1Idx = int(sched1Idx)
	try:
		sched = Schedule.objects.get(pk=sched1Idx)
	except Exception as e:
		errMsg = 'bldSched2: missing schedIdx=%d  ?!' % (sched1Idx)
		print(errMsg)
		return
		
	# sched1: week -> day -> {mtype: move}
	sched1 = sched.details
	meso2 = sched.meso2
	nsession2 = meso2.nsessionWeek
	
	woSched2JSON = {} # week -> day -> {mtype: Movement.pk}

	# FIRST: collect all  Movement mentioned in schedule
	allMoveSet = set()

	for wi in range(meso2.nweek):
		wis = str(wi)
		for si in range(nsession2):
			sis = str(si)
			a1idx = meso2.moveSeq[wis][sis][0]
			allMoveSet.add(int(a1idx))
			a2idx = meso2.moveSeq[wis][sis][1]
			if a2idx != 'OPEN':
				allMoveSet.add(int(a2idx))

	# augment scheduled movements with others to be included		
	for midx in meso2.includeQual:
		allMoveSet.add(int(midx))

	# maintain list of excluded acces
	excludeAccry = [int(eidx) for eidx in meso2.excludeAccry]

	for wi in range(meso2.nweek):
		woSched2JSON[wi] = {}
		
		# NB: Schedule.details JSON dictionary has converted integer indices to strings?
		wis = str(wi)

		for si in range(nsession2):
			
			if meso2.assessNow(wi,si):
				woSched2JSON[wi][si] = {'Assess': 'Assess'}
				continue
								
			sis = str(si)
						
			try:
				# NB: Schedule.details dictionary has converted integer indices to strings?
				a1pk = sched1[wis][sis]['A1']
				preva2pk = sched1[wis][sis]['A2']
				
				# ASSUME: secondary WO are to avoid the previous primary WO, indexed with same sis !
				prevB1pk = sched1[wis][sis]['B1']
				prevB2pk = sched1[wis][sis]['B2']

				a1 = Movement.objects.get(pk=a1pk)
				preva2 = Movement.objects.get(pk=preva2pk)
				prevB1 = Movement.objects.get(pk=prevB1pk)
				prevB2 = Movement.objects.get(pk=prevB2pk)
			except Exception as e:
				errMsg = 'bldSched2: missing some Movement?! wi=%d si=%s %s\n%s' % (wi,si,sched1[wis][sis],e)
				continue
						
			# first B1 is from A1; all allowed because none used day-1
			moveChoiceQS = Movement.objects.all(). \
							filter(mtype='Accessory'). \
							filter(parent=a1pk)
							
			moveChoice1 = list(moveChoiceQS)
			b1 = random.choice(moveChoice1)
			
			# B2, B3: from any primary Measure other than A1,A2
			#			also avoiding any B's from day-1
						
			# print('bldNMSched2: allMove=%s' % (allMoveSet))

			# make copy of allMoveSet, except a1idx, preva2
			otherCandIdx = [aidx for aidx in allMoveSet if (aidx != a1pk and aidx != preva2pk)]

			if len(otherCandIdx) < 2:
				infoStr = 'bldNMSched2: cant select 2 other moves for B2, B3 ?!'
				print(infoStr)
				logger.info(infoStr)
				mo2idx = mo3idx = otherCandIdx[0]
			else:
				sampleList = random.sample(otherCandIdx,2)
				[mo2idx,mo3idx] = sampleList
			
			mo2 = Movement.objects.get(pk=mo2idx)
			mo3 = Movement.objects.get(pk=mo3idx)
			
			mo2kids = list(Movement.objects.filter(parent=mo2))
			mo3kids = list(Movement.objects.filter(parent=mo3))
			
			# exclude any accessories explicitly mentioned in meso
			mo2kidsX = [kid for kid in mo2kids if kid.idx not in excludeAccry]
			mo3kidsX = [kid for kid in mo3kids if kid.idx not in excludeAccry]

			if prevB1 in mo2kidsX:
				mo2kidsX.remove(prevB1)
			if prevB2 in mo2kidsX:
				mo2kidsX.remove(prevB2)
			if len(mo2kidsX) < 1:
				errMsg = 'bldSched2: too few mo2kids parent=%s  ?!' % (mo2idx)
				print(errMsg)
				b2 = b1
			else:
				b2 = random.choice(mo2kidsX)
				
			if prevB1 in mo3kidsX:
				mo3kidsX.remove(prevB1)
			if prevB2 in mo3kidsX:
				mo3kidsX.remove(prevB2)
			if b2 in mo3kidsX:
				mo3kidsX.remove(b2)
				
			if len(mo3kidsX) < 1:
				errMsg = 'bldSched2: too few mo3kids parent=%s  ?!' % (mo3idx)
				print(errMsg)
				b3 = b2
			else:
				b3 = random.choice(mo3kidsX)
			
			# NB: NO  cardio features!
			
			# in secondary, don't ever list a1, a2, only a kid of theirs as b-a1, b-a2
			
			woSched2JSON[wi][si] = {'B1': b1.pk,
							   		'B2': b2.pk,
							   		'B3' :b3.pk }

			infoStr = 'bldNMSched2: wi=%s si=%s a1=%s a2=%s mo2=%s b2=%s mo3=%s b3=%s Nb3Choice=%d' % \
				(wi,si,a1idx,a2idx,mo2idx,b2,mo3idx,b3,len(mo3kidsX))
			print(infoStr)
			logger.info(infoStr)

	sched2 = Schedule()
	sched2.name = sched.name
	sched2.mesoVersion = 'v2'
	sched2.meso2 = meso2
	sched2.stype = 'Secondary'
	sched2.primary = sched
	sched2.details = woSched2JSON
	sched2.save()
	
	return sched2.pk		

def pprintWO(woTbl):
	'''colorized As
	'''
	
# 	woTbl = {mtype: Movement.pk}
	if 'Assess' in woTbl:
		return ( ['Assess'] )

	woNamed = []
	# allMove = list(woTbl.keys())
	# allMove.sort()
	for m in MoveOrder:
		# Meso2:  C not included!
		if m not in woTbl:
			continue
		pk = woTbl[m]
		mobj = Movement.objects.get(pk=pk)
		if m.startswith('A'):
			# NB: use OPEN colors for unknown Measures
			if mobj.name in MeasureColor:
				rgb = MeasureColor[mobj.name]
			else:
				rgb = MeasureColor['OPEN']
				
			ce = '<span style="color:%s">' % rgbColorStr(rgb)
			ce += (mobj.name + '</span>')
			mname = '<b>'+m+':'+ce+'</b>'
		elif m.startswith('B'):
			pobj = mobj.parent
			mname = m+':'+mobj.name+'('+pobj.task+')'
		else:
			mname = m+':'+mobj.name
		woNamed.append(mname)
	return woNamed
	
def pprintSchedNames(sdetails):
	'''convert JSON to comprensible named version
	'''

	schedNamed = {}
	for w in sdetails.keys():
		# NB: JSON produced strings, but views assume ints
		iw = int(w)  
		schedNamed[iw] = {}
		for d in sdetails[w].keys():
			di = int(d)
			woTbl = sdetails[w][d]
			
			woNamed = pprintWO(woTbl)
			
			schedNamed[iw][di] = woNamed
	return schedNamed

def bldUSched(so1,so2):
	
	sched1 = so1.details
	sched2 = so2.details

	meso2 = so1.meso2
	# NB: only COHORTS call bldUSched()
	nweek = meso2.nweek
			
	ncol = len(sched1['0'])+ len(sched2['0'])
	
	usched = {}
	for wi in range(nweek):
		usched[wi] = {}
		wis = str(wi)
		for si in range(ncol):
			if meso2.assessNow(wi,si):
				usched[wi][si] = ['Assess']
				continue
			# even parity ==> sched1
			if si % 2 == 0:
				sis = str(si // 2)
				tbl = sched1[wis][sis]
			else: 
				sis = str((si-1) // 2)
				tbl = sched2[wis][sis]	
				
			usched[wi][si] = tbl
			
	return usched
	
@login_required
def unifiedSched(request,sched1Idx,sched2Idx):

	sched1Idx = int(sched1Idx)
	try:
		so1 = Schedule.objects.get(pk=sched1Idx)
	except Exception as e:
		errMsg = 'unifySched1_2: missing sched1Idx=%s  ?!' % (sched1Idx)
		print(errMsg )
		return render(request,'moveGen/err.html', {'errMsg': errMsg,
													'except': e})

	sched2Idx = int(sched2Idx)
	try:
		so2 = Schedule.objects.get(pk=sched2Idx)
	except Exception as e:
		errMsg = 'unifySched1_2: missing sched2Idx=%s  ?!' % (sched2Idx)
		print(errMsg )
		return render(request,'moveGen/err.html', {'errMsg': errMsg,
													'except': e})

	sched1 = so1.details
	sched2 = so2.details

	meso2 = so1.meso2
	mesoName = meso2.name
	mesoAudience = meso2.audience
	mesoPK = meso2.pk
	# NB: only COHORTS call unifiedSched()
	nweek = meso2.nweek
	nsession = meso2.nsessionWeek
			

	ncol = len(sched1['0'])+ len(sched2['0'])

	usched = bldUSched(so1, so2)
	uschedNamed = pprintSchedNames(usched)
	
	# create weekList and context for schedule template
		
	weekList = []
	for wi in range(nweek):
		dayList = []
		for si in range(ncol):
			elist = []
			for e in uschedNamed[wi][si]:
				if e.startswith('A'):
					elist.append('<b>'+e+'</b>')
				else:
					elist.append(e)
			elistStr = '<li>'.join(elist)
			elistHTML = '<ul><li>' + elistStr + '</ul>'
			dayList.append( elistHTML )
		weekList.append(dayList)

	# NB: Number secondary sessions alphabetically, to distinguish
	
	session1IdxList = [i+1 for i in range(nsession)]
	alphaList = list(string.ascii_uppercase)
	session2IdxList = [alphaList[i] for i in range(len(sched2['0']))]
	
	sessionHdrList = []
	for si in range(ncol):
		# even parity ==> sched1
		if si % 2 == 0:
			sessionHdrList.append(session1IdxList[si // 2])
		else:
			sessionHdrList.append(session2IdxList[(si-1) // 2])

	schedIdxList = []
	for si in range(ncol):
		# even parity ==> sched1
		if si % 2 == 0:
			schedIdxList.append( si // 2)
		else:
			schedIdxList.append( (si-1) // 2)
				
	context = {'mesoName': mesoName,
				'mesoIdx': mesoPK,
				'mesoAudience': mesoAudience,
				'stype': 'Unified',
				'schedName': so1.name,
				'weekList': weekList,
				'nsession': ncol,
				'sessionHdrList': sessionHdrList,
				'schedIdxList': schedIdxList,
				'sched1Idx': sched1Idx,
				'sched2Idx': sched2Idx}
	return render(request, 'moveGen/schedule.html', context)


@login_required
def toc(request):
	'''Produce Meso -> Sched -> Primary, Secondary, Unified table of contents
	satisfying toc.html template columns
	MesoName,MesoDesc,SchedIdx,SchedCreateDate,SchedName,Primary,Secondary,Unified
	180304: include Meso2
	'''

	mschedList = []

	# put newer Meso2 first in TOC
	meso2qs = MesoCycle2.objects.all()
	meso2List = list(meso2qs)
	for meso2 in meso2List:
		schedqs = Schedule.objects.all(). \
					filter(meso2_id=meso2.pk). \
					filter(stype='Primary'). \
					order_by('cdate').reverse()
		schedList = list(schedqs)
		
		if len(schedList) == 0:
			row = {}
			row['meso2PK'] = meso2.pk
			row['mesoName'] = meso2.name
			row['mesoAudience'] = meso2.audience
			row['schedPK'] = ''
			row['schedCDate'] = ''
			row['schedName'] = '(no schedules yet)'
			row['sched2PK'] = None
			row['schedEval'] = ''
			mschedList.append(row)
			infoStr = 'toc: no schedules for meso2=%d' % (meso2.pk)
			print(infoStr)
			logger.info(infoStr)
			continue
			
		for si,sched in enumerate(schedList):
			sched2 = Schedule.objects.all(). \
						filter(primary=sched.pk). \
						filter(stype='Secondary')
						
			ns2 = sched2.count()
			if ns2 == 0:
				# no secondary sched built
				s2pk = None
			elif ns2 == 1:
				s2o = list(sched2)[0]
				if s2o == None:
					infoStr = 'toc: null singleton!',sched.pk,ns2
					print(infoStr)
					logger.info(infoStr)
					s2pk = None
				else:
					s2pk = s2o.pk
			else:
				infoStr = 'toc: multiple Sched2?!',sched.pk
				print(infoStr)
				logger.info(infoStr)
				allSched2 = list(sched2)
				for s in allSched2:
					infoStr = s.pk,s.name,s.primary.pk
					print(infoStr)
					logger.info(infoStr)
				# NB: randomly pick FIRST one associated w/ primary (:
				s2pk = allSched2[0].pk
					
			row = {}
			row['meso2PK'] = meso2.pk
			row['mesoName'] = meso2.name
			row['mesoAudience'] = meso2.audience
			row['schedPK'] = sched.pk
			row['schedCDate'] = sched.cdate
			row['schedName'] = sched.name
			row['sched2PK'] = s2pk
						
			mschedList.append(row)

	context = {'mschedList': mschedList}
	
	return render(request, 'moveGen/toc.html', context)

def freqHist3(tbl):
	"Assuming values are frequencies, returns sorted list of (val,freq) items in descending freq order"
	from functools import cmp_to_key
	def cmpd1(a,b):
		"decreasing order of frequencies"
		return b[1] - a[1]

	
	flist = list(tbl.items()) #python3
	flist.sort(key=cmp_to_key(cmpd1))
	return flist

def entropy(dist):
	'compute (log2 ==> bits) entropy over distribution'

	h = 0.
	tot = sum(dist)
	if tot == 0:
		return h
	
	for n in dist:
		if n > 0:
			nf = float(n)
			p = nf/tot
			h -= p * math.log(p,2)
	return h
	
def evalSched(schedDetails):
	'''Evaluation distribution of movements within primary schedule
	'''
	
	
	moveFreq = {}
	allMove = list(Movement.objects.all().exclude(mtype='Exercise'))
	for pk in [mo.pk for mo in allMove]:
		moveFreq[pk] = 0
	
	children = defaultdict(set) # measureMove -> {accessMove}
	for w in schedDetails.keys():
		for d in schedDetails[w].keys():
			woTbl = schedDetails[w][d]
			allMove = list(woTbl.keys())
			allMove.sort()
			for m in allMove:
				if m=='Assess':
					continue
				pk = woTbl[m]
				moveFreq[pk] += 1
				if Movement.objects.get(pk=pk).parent != None:
					ppk = Movement.objects.get(pk=pk).parent.pk
					moveFreq[ppk] += 1
					children[ppk].add(pk)

	allMeasure = list(children.keys())
	allMeasure.sort(key=lambda k: moveFreq[k],reverse=True)
	for mmpk in allMeasure:
		mo = Movement.objects.get(pk=mmpk)
		infoStr = '%d\t%s' % (moveFreq[mmpk],mo.name)
		print(infoStr)
		logger.info(infoStr)
		allchildren = list(children[mmpk])  # list vs set
		allchildren.sort(key=lambda k: moveFreq[k],reverse=True)
		for ampk in allchildren:
			mo = Movement.objects.get(pk=ampk)
			infoStr = '%d\t\t%s' % (moveFreq[ampk],mo.name)
			print(infoStr)
			logger.info(infoStr)
		
	e = entropy(moveFreq.values())
	infoStr = 'E=',e
	print(infoStr)
	logger.info(infoStr)
	
	return e

@login_required
def showSchedDist(request,sched1Idx):
	'''Show distribution of movements within primary schedule
	'''
	
	schedIdx = int(sched1Idx)
	sched = Schedule.objects.get(idx=schedIdx)
	
	schedDetails = sched.details
	
	moveFreq = {}
	allMove = list(Movement.objects.all().exclude(mtype='Exercise'))
	for pk in [mo.pk for mo in allMove]:
		moveFreq[pk] = 0
	
	children = defaultdict(set) # measureMove -> {accessMove}
	for w in schedDetails.keys():
		for d in schedDetails[w].keys():
			woTbl = schedDetails[w][d]
			allMove = list(woTbl.keys())
			allMove.sort()
			for m in allMove:
				if m=='Assess':
					continue
				pk = woTbl[m]
				moveFreq[pk] += 1
				if Movement.objects.get(pk=pk).parent != None:
					ppk = Movement.objects.get(pk=pk).parent.pk
					moveFreq[ppk] += 1
					children[ppk].add(pk)

	outFreq = [] # [ (lbl,freq) ]
	allMeasure = list(children.keys())
	# allMeasure.sort(key=lambda k: moveFreq[k],reverse=True)
	allMeasure.sort(key=lambda k: Movement.objects.get(pk=k).name)
	hspan= 4*'&emsp;'
	for mmpk in allMeasure:
		mo1 = Movement.objects.get(pk=mmpk)
		mlist = [mo1.name]
		f1 = moveFreq[mmpk]
		# print('%d\t%s' % (moveFreq[mmpk],mo.name))
		allchildren = list(children[mmpk])  # list vs set
		# allchildren.sort(key=lambda k: moveFreq[k],reverse=True)
		outFreq.append( ['<b>'+mo1.name+'</b>', f1] )
		childrenum = 0
		allchildren.sort(key=lambda k: Movement.objects.get(pk=k).name)
		for ampk in allchildren:
			mo2 = Movement.objects.get(pk=ampk)
			f2 = moveFreq[ampk]
			childrenum += f2
			# print('%d\t\t%s' % (moveFreq[ampk],mo.name))
			outFreq.append([hspan+mo2.name, f2])
		outFreq.append([hspan+'(direct)', f1-childrenum])
		
	e = entropy(moveFreq.values())
	
	context = {}
	context['schedIdx'] = schedIdx
	context['schedName'] = sched.name
	context['outFreq'] = outFreq
	context['e'] = '%6.2f' % (e)
	
	return render(request, 'moveGen/showSchedDist.html', context)

def clientAssess(request, clientIdx):
	context = {'clientIdx': clientIdx}
	return render(request, 'moveGen/assessClient.html', context)

def  getOtherMovesInfo(woDetails):
	'''return list of moveInfo for all (non-Exercise) movements NOT included in woDetails
	'''
	
	woMovePKList = [woDetails[mt] for mt in woDetails.keys()]
	
	otherDetails = []
	for move in Movement.objects.all():
		if move.mtype=='Exercise':
			continue
		if move.idx not in woMovePKList:
			moveInfo ={}
			for f in ['idx','name','mtype']:
				moveInfo[f] = getattr(move,f)
			if move.mtype=='Accessory':
				pobj = move.parent
				moveInfo['parent'] = pobj.name
			else:
				moveInfo['parent'] = move.name
			otherDetails.append( moveInfo)
	return otherDetails

def  getMovesInfo(woDetails):
	'''return list of moveInfo for movements
	'''
	
	details = []
	for woRole,idx in woDetails.items():
		move = Movement.objects.get(idx=idx)
		moveInfo ={}
		for f in ['idx','name','mtype']:
			moveInfo[f] = getattr(move,f)
		moveInfo['woRole'] = woRole
		if move.mtype=='Accessory':
			pobj = move.parent
			moveInfo['parent'] = pobj.name
		else:
			moveInfo['parent'] = move.name
		details.append( moveInfo)
	return details

def  getOtherExer(woExerPKList,schedDetails,excludeAccryList):
	'''return list of EXERCISES for movements NOT included in woExerPKList
	   but constrained to other movements from schedDetails
	   
	   180405: OnlyMesoMentions parameter allows switching betweem all/mentioned
	'''
		
	schedMeasureSet = set()
	for wis in schedDetails.keys():
		weekDetails = schedDetails[wis]
		for sis in weekDetails.keys():
			for mtype in schedDetails[wis][sis]:
				if mtype == 'Assess':
					continue
				elif mtype.startswith('A'):
					idx = schedDetails[wis][sis][mtype]
					move = Movement.objects.get(idx=idx)
					if move.mtype=='Measure':
						schedMeasureSet.add(move)		

	otherDetails = []
	for exer in Movement.objects.filter(mtype='Exercise'):
		if exer.idx in woExerPKList:
			continue
	
		if exer.parent == None:
			infoStr = 'getOtherExer: exer w/o parent?! %s %s' % (exer.idx,exer.name)
			print(infoStr)
			logger.info(infoStr);
			continue	
		aobj = exer.parent
		
		# 180407: don't include any excercises from explicitly excluded accessories
		if aobj.idx in excludeAccryList:
			continue
		
		mobj = aobj.parent
		if mobj not in schedMeasureSet:
			continue
		
		exerInfo = {}
		exerInfo['measure'] = mobj.name
		exerInfo['access'] = aobj.name
		for f in ['idx','name']:
			exerInfo[f] = getattr(exer,f)
		exerInfo['woRole'] = ''
		
		otherDetails.append(exerInfo)
	return otherDetails

def  getMovesExer(woDetails):
	'''return list of EXERCISES for movements in morder
	'''
	
	details = []
	# NB: always listed in MoveOrder
	for woRole in MoveOrder:
		# NB: Supplementary workouts won't have A's
		if woRole not in woDetails:
			continue
		idx = woDetails[woRole]
		move = Movement.objects.get(idx=idx)
		
		# NB: when a meausure is included, *IT* is the exercise
		if move.mtype=='Measure':			
			exerInfo = {}
			exerInfo['measure'] = move.name
			exerInfo['access'] = ''
			exerInfo['idx'] = move.idx
			exerInfo['name'] = move.name
			exerInfo['woRole'] = woRole
			
			details.append(exerInfo)
			
			continue
		
		measure = move.parent

		exerqs = Movement.objects.filter(parent=idx)
		exerList = list(exerqs)
		for exer in exerList:
			exerInfo = {}
			exerInfo['measure'] = measure.name
			exerInfo['access'] = move.name
			exerInfo['idx'] = exer.idx
			exerInfo['name'] = exer.name
			exerInfo['woRole'] = woRole
			
			details.append(exerInfo)
			
	return details

@login_required
def drawWOS(request,schedIdx,week,dayStr):
	'''v2: 	mesoAudience=indiv: all workouts reference same PRIMARY
			mesoAudience=cohort: day is wrt/ either primary or secondary schedIdx
				need to build and provide same dayList context in either case
	'''
	
	# NB: week, day are strings; correct as indices into details
	so = Schedule.objects.get(pk=schedIdx)
	
	meso = so.meso2
	mesoAudience = so.meso2.audience
	excludeAccryList = meso.excludeAccry
		
	woDetails = so.details[week][dayStr]
	
	day = int(dayStr)
	if mesoAudience=='indiv':
		# NB: increment dayLbl for human consumption; 
		# week incremented via {{week|add:"1"}}
		dayIdx = day+1
		dayLbl = str(dayIdx)
		so1 = so
		# so2 irrelevant to Primary WOS
		so2 = None
		
		sched1 = so1.details
		ncol = len(sched1['0'])
		schedNamed = pprintSchedNames(so1.details)

		woExer = getMovesExer(woDetails) # list of HTML strings
		woExerPKList = [exer['idx'] for exer in woExer]
		otherExer = getOtherExer(woExerPKList,so1.details,excludeAccryList) # list of moveInfo
		# sort by measure type
		otherExer.sort(key=lambda m: m['measure']+m['access'])

	else:
		alphaList = list(string.ascii_uppercase)
		
		if so.stype == 'Primary':
			so1 = so
			# NB: only one secondary Schedule should have this primary
			so2 =  Schedule.objects.get(primary=schedIdx)
			
			dayLbl = str(day+1)
			dayIdx = (day * 2)+1 
						
		else:
			so1 = so.primary
			so2 = so
			
			dayLbl = alphaList[day]
			dayIdx = 2 * day + 2

		woExer = getMovesExer(woDetails) # list of HTML strings
		woExerPKList = [exer['idx'] for exer in woExer]
		otherExer = getOtherExer(woExerPKList,so1.details,excludeAccryList) # list of moveInfo
		# sort by measure type
		otherExer.sort(key=lambda m: m['measure']+m['access'])

		sched1 = so1.details
		sched2 = so2.details
		ncol = len(sched1['0'])+ len(sched2['0'])
		usched = bldUSched(so1,so2)
		schedNamed = pprintSchedNames(usched)
	
	dayList = []
	wi = int(week)
	for si in range(ncol):
		elist = schedNamed[wi][si]

		elistStr = '<li>'.join(elist)
		elistHTML = '<ul><li>' + elistStr + '</ul>'
		dayList.append( elistHTML )


	context = {}
	context['meso'] = meso
	context['mesoAudience'] = mesoAudience
	context['week'] = int(week)
	context['dayIdx'] = dayIdx
	context['dayLbl'] = dayLbl
	context['schedIdx'] = schedIdx
	context['schedName'] = so.name
	context['stype'] = so.stype
	context['dayList'] = dayList
	context['woExer'] = woExer
	context['otherExer'] = otherExer
	
	return render(request, 'moveGen/drawWOS.html', context)

@login_required
def saveWOS(request):
	# request.POST['schedList'] = JSON string =  [{"measure":"Assault Bike","access":"Glycolytic (~1min)","idx":955,"name":"Complex (BB, KB, bw)","woRole":"","x":338,"y":213,"nrep":1},
	# 												{"measure":"Push-Up","access":"Plank","idx":968,"name":"SA Plank","woRole":"","x":429,"y":355,"nrep":2},{"measure":"Split Squat","access":"Single Leg Stability","idx":974,"name":"Walking Lunge","woRole":"","x":436,"y":275,"nrep":3},{"measure":"TB Deadlift","access":"submax effort TB DL (concentric only)","idx":975,"name":"5 x 3","woRole":"","x":343,"y":593,"nrep":4}]

	author = request.user
	mesoIdx = request.POST['mesoIdx'] # meso-initMeso-5
	# mesoBits = mesoStr.split('-')
	# mesoIdx = int(mesoBits[2])
	week = int(request.POST['week'])
	dayIdx = int(request.POST['dayIdx'])
	schedIdx = int(request.POST['schedIdx'])
	schedList = json.loads(request.POST['schedList'])
	
	defaultCD = {"access": "CoolDown", 
					"measure": "CoolDown", 
					"name": "CoolDown", 
					"woRole": "CD", 
					"idx": 0,
					"nrep": 0,
					"x": 0, 
					"y": 0 }
			
	wos = Workout()
	sched = Schedule.objects.get(pk=schedIdx)
	wos.sched = sched
	# NB: only WOS dependence is on meso/2's NAME
	wos.meso2 = MesoCycle2.objects.get(pk=mesoIdx)
	mesoName = sched.meso2.name
	
	wos.author = author
	wos.week = week

	# 180322: dayIdx from drawWOS.html is human-readable 1-based index		
	wos.day = dayIdx-1
	
	wos.schedList = schedList
	
	wos.save()

	# NB: need to make context for WOSgraphic.html template consistent with showWOS()
	if sched.stype == 'Primary':
		# NB: increment dayLbl for human consumption; 
		# week incremented via {{week|add:"1"}}
		# 170118: dayIdx is already set correctly in drawWOS()
		day2 = (dayIdx // 2) + 1
		dayLbl = str(day2)
	else:
		# 170118: dayIdx needs to be converted BACK (:
		day2 = (dayIdx-1) // 2
		alphaList = list(string.ascii_uppercase)
		dayLbl = alphaList[day2]
	
	context = {}
	context['wosIdx'] = wos.idx
	context['mesoName'] = mesoName
	context['week'] = week
	context['schedIdx'] = schedIdx
	context['schedName'] = sched.name
	context['dayLbl'] = dayLbl
	# NB: need to convert schedList BACK to JSON for template
	context['schedList'] = json.dumps(schedList)
	context['stype'] = sched.stype

	return render(request, 'moveGen/WOSgraphic.html', context)

@login_required
def allWOS(request,sched1Idx,sched2Idx=None):

	sched1Idx = int(sched1Idx)
	try:
		so1 = Schedule.objects.get(pk=sched1Idx)
	except Exception as e:
		errMsg = 'allWOS: missing sched1Idx=%s  ?!' % (sched1Idx)
		print(errMsg )
		return render(request,'moveGen/err.html', {'errMsg': errMsg,
													'except': e})
	meso2 = so1.meso2
	mesoName = meso2.name
	mesoPK = meso2.pk
	mesoAudience = meso2.audience
	if meso2.audience == 'indiv':
		nweek = 1
		nsession = meso2.totSession
		indiv = True
	elif meso2.audience == 'cohort':
		nweek = meso2.nweek
		nsession = meso2.nsessionWeek
		indiv = False
			
	sched1 = so1.details

	if indiv:
		ncol = len(sched1['0'])
		sessionHdrList = [i+1 for i in range(nsession)]

		weekList = []
		for wi in range(nweek):
			dayList = []
			for si in range(ncol):
					
				woqs = Workout.objects.filter(sched=sched1Idx) \
										.filter(week=wi) \
										.filter(day=si)
				wolist = list(woqs)
				if len(wolist) == 0:
					# dayList.append('<em>(None)</em>')
					cell = '<em>(None)</em>'
				elif len(wolist) == 1:
					wo = wolist[0]
					wodate = wo.createDate
					dateStr = wodate.strftime('%b %d %Y')
					lbl = wo.author + ' (%s)' % (dateStr)
					anchor = '<a href="/moveGen/showWOS/%d">%s</a>' % (wo.idx,lbl) 
					# dayList.append(anchor)
					cell = anchor
				else:
					elist = []
					for wo in wolist:
						wodate = wo.createDate
						dateStr = wodate.strftime('%b %d %Y')
						lbl = wo.author + ' (%s)' % (dateStr)
						anchor = '<a href="/moveGen/showWOS/%d">%s</a>' % (wo.idx,lbl) 
						elist.append(anchor)				
					elistStr = '<li>'.join(elist)
					elistHTML = '<ul><li>' + elistStr + '</ul>'
					# dayList.append( elistHTML )
					cell = elistHTML
	
				drawWOSLink = '<p><a href="/moveGen/drawWOS/%d_%d_%d" style="color:#FF0000;">Draw WOS</a></p>' % (sched1Idx,wi,si)
				cell += drawWOSLink
				
				dayList.append(cell)
					
			weekList.append(dayList)
		
	else:
		sched2Idx = int(sched2Idx)
		try:
			so2 = Schedule.objects.get(pk=sched2Idx)
		except Exception as e:
			errMsg = 'allWOS: missing sched2Idx=%s  ?!' % (sched2Idx)
			print(errMsg )
			return render(request,'moveGen/err.html', {'errMsg': errMsg,
														'except': e})
	
		sched2 = so2.details
		
		ncol = len(sched1['0'])+ len(sched2['0'])
	
		session1IdxList = [i+1 for i in range(nsession)]
		alphaList = list(string.ascii_uppercase)
		session2IdxList = [alphaList[i] for i in range(len(sched2['0']))]
		
		sessionHdrList = []
		for si in range(ncol):
			# even parity ==> sched1
			if si % 2 == 0:
				sessionHdrList.append(session1IdxList[si // 2])
			else:
				sessionHdrList.append(session2IdxList[(si-1) // 2])
	
		weekList = []
		for wi in range(nweek):
			dayList = []
			for si in range(ncol):
	
				# Add link to drawWOS
				if si % 2 == 0:
					schedIdx = sched1Idx
					sis = si // 2
				else:
					schedIdx = sched2Idx
					sis = (si-1) // 2
				
				woqs = Workout.objects.filter(sched=schedIdx) \
										.filter(week=wi) \
										.filter(day=si)
				wolist = list(woqs)
				if len(wolist) == 0:
					# dayList.append('<em>(None)</em>')
					cell = '<em>(None)</em>'
				elif len(wolist) == 1:
					wo = wolist[0]
					wodate = wo.createDate
					dateStr = wodate.strftime('%b %d %Y')
					lbl = wo.author + ' (%s)' % (dateStr)
					anchor = '<a href="/moveGen/showWOS/%d">%s</a>' % (wo.idx,lbl) 
					# dayList.append(anchor)
					cell = anchor
				else:
					elist = []
					for wo in wolist:
						wodate = wo.createDate
						dateStr = wodate.strftime('%b %d %Y')
						lbl = wo.author + ' (%s)' % (dateStr)
						anchor = '<a href="/moveGen/showWOS/%d">%s</a>' % (wo.idx,lbl) 
						elist.append(anchor)				
					elistStr = '<li>'.join(elist)
					elistHTML = '<ul><li>' + elistStr + '</ul>'
					# dayList.append( elistHTML )
					cell = elistHTML
	
				drawWOSLink = '<p><a href="/moveGen/drawWOS/%d_%d_%d" style="color:#FF0000;">Draw WOS</a></p>' % (schedIdx,wi,sis)
				cell += drawWOSLink
				
				dayList.append(cell)
					
			weekList.append(dayList)
	
		schedIdxList = []
		for si in range(ncol):
			# even parity ==> sched1
			if si % 2 == 0:
				schedIdxList.append( si // 2)
			else:
				schedIdxList.append( (si-1) // 2)

	context = {'mesoName': mesoName,
				'mesoIdx': mesoPK,
				'mesoAudience': mesoAudience,
				'stype': 'allWOS',
				'schedName': so1.name,
				'weekList': weekList,
				'nsession': ncol,
				'sessionHdrList': sessionHdrList,
				'sched1Idx': sched1Idx,
				'sched2Idx': sched2Idx}
	return render(request, 'moveGen/schedule.html', context)

@login_required
def showWOS(request,wosIdx):
	wosIdx = int(wosIdx)
	try:
		wos = Workout.objects.get(pk=wosIdx)
	except Exception as e:
		errMsg = 'showWOS: missing wosIdx=%s  ?!' % (wosIdx)
		print(errMsg )
		return render(request,'moveGen/err.html', {'errMsg': errMsg,
													'except': e})

	if request.method == 'POST':

		evalr = request.user.username
		postEval = request.POST['wosEval']
		evalComment = request.POST['wosComment']
		
		wosEval = WOSEval()
		wosEval.workout = wos
		try:
			wosEval.eval = int(postEval)
		except Exception as e:
			wosEval.eval = 0
			
		wosEval.comment = evalComment
		wosEval.evaluator = evalr
		wosEval.save()
	
		context = {}
		context['wosIdx'] = wosIdx
		context['eval'] = wosEval.eval
		context['comments'] = wosEval.comments

		return render(request, 'moveGen/evalWOSconfirm.html', context)

	# Non-post: first display prior to evaluation
	
	sched = wos.sched
	schedIdx = sched.idx
	schedName = sched.name

	# NB: only WOS dependence is on meso/2's NAME
	mesoName = sched.meso2.name
			
	day = wos.day
	if sched.stype == 'Primary':
		# NB: increment dayLbl for human consumption; 
		# week incremented via {{week|add:"1"}}
		# 170118: day is already set correctly in drawWOS(),saveWOS()
		day2 = (day // 2) + 1
		dayLbl = str(day2)
	else:
		# 170118: day needs to be converted BACK (:
		day2 = (day) // 2
		alphaList = list(string.ascii_uppercase)
		dayLbl = alphaList[int(day2)]

	# NB: need to make context for WOSgraphic.html template consistent with showWOS()
		
	context = {}
	context['wosIdx'] = wosIdx
	context['mesoName'] = mesoName
	context['week'] = wos.week
	context['schedIdx'] = schedIdx
	context['schedName'] = schedName
	context['dayLbl'] = dayLbl
	# NB: need to convert schedList BACK to JSON for template
	context['schedList'] = json.dumps(wos.schedList)
	context['stype'] = sched.stype
		
	return render(request, 'moveGen/WOSgraphic.html', context)

class DotDict(dict):
	""" https://stackoverflow.com/a/23689767
	dot.notation access to dictionary attributes"""


	__getattr__ = dict.__getitem__
	__setattr__ = dict.__setitem__
	__delattr__ = dict.__delitem__

def moves2dict(moveList):
	'''create dictionary of all movements, for editing, comparing, ...
		formatted as expected by d3.hierarchy
		modified to accept list of dict WITH PARENT dict, as produced by saveDefaultMoves command
		
		2do:  Only meed moveDict[0], need to produce the rest of the idx->Movement items?
	'''

# 	allMoveObj = Movement.objects.all()
# 	allMoveList = list(allMoveObj)
	
	moveDict = {} # idx -> {}
	moveDict[0] = {'idx': 0, 'name': 'Movements', 'children':[]}
	for mdict in moveList:
		# HACK just to leave dot notation from v0
		mo = DotDict(mdict)
		if mo.idx not in moveDict:
			if mo.mtype == 'Measure':
				mname = measureName(mo)
			else:
				mname = mo.name
			m = {'idx': mo.idx, 'name': mname, 'mtype': mo.mtype, 'children':[]}
			moveDict[mo.idx] = m
		m = moveDict[mo.idx]
			
		if mo.parent == None:
			pkey = 0  # root
		else:
			# HACK just to leave dot notation from v0
			po = DotDict(mo.parent)
			pkey = po.idx
			if pkey not in moveDict:
				if mo.parent.mtype == 'Measure':
					pname = measureName(po)
				else:
					pname = po.name

				pm = {'idx': pkey, 'name': pname, 'mtype': po.mtype, 'children':[]}
				moveDict[pkey] = pm
				
		moveDict[pkey]['children'].append(m)
		
	def sortKids(idx):
		'''recursive in-place sorting of all kids, lexicographic on name
		'''
		nd = moveDict[idx]
		
		for kid in nd['children']:
			kidx = kid['idx']
			sortKids(kidx)
			
		nd['children'].sort(key=(lambda nd: nd['name']))
		
	sortKids(0)
	
	return moveDict
	
@login_required
def editMoves(request,mesoSysPK):
		
	# moveDict = moves2dict()
	
	if mesoSysPK == 'NEW':
		ms = MesoSystem()
		ms.name = "NewMeso"
		ms.author = request.user
		# cf moves2dict()
		moveDict = {'idx': 0, 'name': 'Movements', 'children':[]}
		ms.moveDict = moveDict
		ms.save()
	else:
		ms = MesoSystem.objects.get(idx=mesoSysPK)
		moveDict = ms.moveDict
	
	context = {}
	context['mesoSys'] = ms
	context['moveDict'] = json.dumps(moveDict)
		
	return render(request, 'moveGen/editMoves.html', context)



# 2do: Refactor: make these methods of model.Movement
def measureName(move):
	return '%s // %s' % (move.task,move.name)

def splitMeasureName(nname):
	''' ala task, mname = splitMeasureName(mname)
	'''
	
	task, mname = nname.split('//')
	mname = mname.strip()
	task = task.strip()
	return task,mname

# NB: These need to be global because of reference within recursive preorder()
Chg2applyList = []

def bldChg2ApplyList(moveDict):
	'''Create list of movement adds and name changes of mesoSys.moveDict
	relative to current state of Movements database table
	
	requires any new parents exist before new kids can refer to them ==> prefix traversal
	'''
	global Chg2applyList
	
	def preorder(nd,pidx):
		global Chg2applyList
		nname = nd['name']
		mtype = nd['mtype']
		ndIdx = nd['idx']
		# idx = int(idxs)
		
		if ndIdx < 0:
			try:
				if mtype=='Measure': # depth==1:
					task, mname = splitMeasureName(nname)
					mname = mname.strip()
					task = task.strip()
				else:
					mname = nname
					task = ''
					
	
				chgSpec = {'chgType': 'add', 'idx': ndIdx,'name': mname, 'mtype': mtype,
							'task': task, 'pidx': pidx} 
				Chg2applyList.append(chgSpec)

				infoStr = 'bldChg2ApplyList1: "%s"' % (chgSpec)
				print(infoStr)
				logger.info(infoStr)
												
			except Exception as e:
				infoStr = 'bldChg2ApplyList: cant save Movement?!',ndIdx,nd,e
				print(infoStr)
				logger.info(infoStr)
		
		elif ndIdx != 0:
			try:
				prevMove = Movement.objects.get(idx=ndIdx)
			except Exception as e:
				infoStr = 'bldChg2ApplyList: bad Movement idx?!',ndIdx,nd,e
				print(infoStr)
				logger.info(infoStr)

			if prevMove.mtype == 'Measure':
				prevname = measureName(prevMove)
			else:
				prevname = prevMove.name
		
			if prevname != nname:
	
				# update existing move's name
				if mtype != prevMove.mtype:
					infoStr = 'bldChg2ApplyList: moveType not consistent?! id=%s %s,%s -> %s,%s' % \
							(ndIdx,prevname,prevMove.mtype,nname,mtype)
					print(infoStr)
					logger.info(infoStr)
				else:
					prevMove.name = nname
					
					chgSpec = {'chgType': 'chg', 'idx': ndIdx,'name': nname,'prevname': prevname} 
					Chg2applyList.append(chgSpec)
					infoStr = 'bldChg2ApplyList2: "%s"' % (chgSpec)
					print(infoStr)
					logger.info(infoStr)
				
		for kidx in nd['children']:
			# kidxs = str(kidx)
			###
			knd = preorder(kidx,ndIdx)
			###
			
		return nd['idx']
	
	Chg2applyList = []	
	
	# NB: mesoSys name now changed immediately in previewMoveEdits()

	# NB: Root movement 'Movements' idx=0		
	###
	for kid in moveDict['children']:
		# kidxs = str(kidx)
		knd = preorder(kid,0)
	###

	return Chg2applyList

def sortMoveDict(moveDict):
	'''recursive sort of moves based on names
	'''	

	def preorder(nd):
		
		newKids = copy.deepcopy(nd['children'])
		newKids.sort(key=lambda k: k['name'])
		
		kidNames = [k['name'] for k in nd['children']]
		newNames = [k['name'] for k in newKids]
# 		if kidNames != newNames:
# 			print('sortMoveDict:',nd['name'],newKids)
			
		nd['children'] = newKids
		
		for kid in nd['children']:
			preorder(kid)
			
		return nd

	sortedMoves = {"name":"Movements","idx":0,'children':[]}
	newKids = copy.deepcopy(moveDict['children'])
	# NB: top-level Quality/Assessed tasks sorted on TASK!
	
	newKids.sort(key=lambda k: splitMeasureName(k['name'])[0])

	kidNames = [k['name'] for k in moveDict['children']]
	newNames = [k['name'] for k in newKids]
# 	if kidNames != newNames:
# 		print('sortMoveDict:',moveDict['name'],newKids)
	
	for kid in newKids:
		###
		sortedMoves['children'].append( preorder(kid) )
	
	return sortedMoves

	
def previewMoveEdits(request,mesoSysPK):
	'''Compare newMoves to current Movements table
		Create list of modified names or new moves flagged with large negative idx
		DOESNT COMMIT THE Movements CHANGES; just bldChg2ApplyList() and show in previewEditMoves.html
		DOES update mesoSys with newMoves, MesoSys NAME
	
	requires any new parents exist before new kids can refer to them ==> prefix traversal by bldChg2ApplyList()

	'''
	
	global Chg2applyList
	
	userName = request.user.get_username()
	mesoSys = MesoSystem.objects.get(pk=mesoSysPK)

	msNameChange = False
	newMSName = request.POST['msName']

	# NB: chg2applyList cannot capture mesoSys name change!  only reflected in confListHTML
	if newMSName != mesoSys.name:
		msNameChange = True
		infoStr = 'user=%s previewMoveEdits MesoSys name changed %s --> %s' % (userName,mesoSys.name,newMSName)
		print(infoStr)
		logger.info(infoStr)
		mesoSys.name = newMSName
		mesoSys.save()
		
	newMoveStr = request.POST['newMoves']
	newMoves = json.loads(newMoveStr)

	sortedMoves = sortMoveDict(newMoves)
	
	mesoSys.moveDict = sortedMoves
	mesoSys.save()

	chg2applyList = bldChg2ApplyList(mesoSys.moveDict)
	
	if msNameChange:
		confListHTML = changeList2HTML(chg2applyList,newMSName)
	else:
		confListHTML = changeList2HTML(chg2applyList)
		
	context = {}
	context['mesoSys'] = mesoSys
	context['confList'] = confListHTML
	context['changes2apply'] = json.dumps(Chg2applyList)
	
	return render(request, 'moveGen/previewMoveEdits.html', context)

def changeList2HTML(changeList,newMSName=''):
	confListHTML = '<ul>\n'
	if newMSName != '':
		chgHTML = '<li><b>MesoSys NAME CHANGE</b> to %s</li>\n' % (newMSName)
		confListHTML += chgHTML
		
	for chgSpec in changeList:
		if chgSpec['chgType'] == 'add':
			mtype = chgSpec['mtype']
			if mtype == 'Measure':
				chgHTML = '<li><b>ADD</b> %s %s // %s %s Parent:%s</li>\n' % \
				(chgSpec['idx'],chgSpec['task'],chgSpec['name'],mtype,chgSpec['pidx'])
			else:
				chgHTML = '<li><b>ADD</b> %s %s %s Parent:%s</li>\n' % \
				(chgSpec['idx'],chgSpec['name'],mtype,chgSpec['pidx'])	
		elif chgSpec['chgType'] == 'chg':
			chgHTML = '<li><b>NAME CHANGE</b> %s %s <-- %s</li>\n' % \
			(chgSpec['idx'],chgSpec['name'],chgSpec['prevname'])
		elif chgSpec['chgType'] == 'msName':
			chgHTML = '<li><b>MesoSys NAME CHANGE</b> %s %s <-- %s</li>\n' % \
			(chgSpec['idx'],chgSpec['name'],chgSpec['prevname'])

		confListHTML += chgHTML
	confListHTML += '</ul>'
	
	return confListHTML

def applyMoveEdits(request,mesoSysPK):
	'''Apply Movement edits from editMoves() and confirmed by previewEditMoves()
		via changes2apply POST variable 
		modify mesoSys moveDict with updated indices for new Movements
	'''

	def updateIdx(prevMoves,newIDTbl):
		'''replace temporary negative indices with new ones
		remove pidx as inclusion via 'children' suffices
		'''
		
		def preorder(prevnd):
			prevIdx = prevnd['idx']
	
			if prevIdx < 0:
				if prevIdx not in newIDTbl:
					infoStr = 'updateIdx: missing prevIdx?!',prevIdx
					print(infoStr)
					logger.info(infoStr)
					newIdx = prevIdx
				else:
					newIdx = newIDTbl[prevIdx]
			else:
				newIdx = prevIdx
				
			newnd = copy.deepcopy(prevnd)
			newnd['idx'] = newIdx
			
			# newnd['pidx'] = newIDTbl[ prevnd['pidx'] ]
			# remove pidx as inclusion via 'children' suffices
			del(newnd['pidx'])
			
			newnd['children'] = []
			
			for kid in prevnd['children']:
				newnd['children'].append( preorder(kid) )
				
			return newnd
						
		assert prevMoves['idx']==0 and prevMoves['name'] == "Movements", 'updateIdx: bad root ?!'
		
		newMoves = {"name":"Movements","idx":0,"children":[]}
				
		for kid in prevMoves['children']:
			###
			newMoves['children'].append( preorder(kid) )
	
		return newMoves

	mesoSys = MesoSystem.objects.get(idx=mesoSysPK)	

	editMoveDict = mesoSys.moveDict
	chg2apply = bldChg2ApplyList(editMoveDict)
	
	userName = request.user.get_username()
	sh_tHappened = False
	
	# ASSUME chg2apply list still in  preorder, so parents will exist before reference	
	newIDTbl = {}

	for chgSpec in chg2apply:
		try:	
			# NB: truncate name to satisfy models.Movement.name: max_length=50
			moveName = chgSpec['name'][:45]
			
			if chgSpec['chgType'] == 'add':
				tmpidx = chgSpec['idx']
				newMove = Movement()
				newMove.name = moveName
				
				newMove.task = chgSpec['task']
				newMove.mtype =  chgSpec['mtype'] # MoveDepth2Type[]
				pidx = chgSpec['pidx']
				if pidx < 0:
					pidx = newIDTbl[pidx]
				if pidx == 0 or pidx == None:
					newMove.parent = None
					chgSpec['pidx'] = None
				else:
					po = Movement.objects.get(idx=pidx)
					newMove.parent = po
					# HACK: use pidx for parent NAME in changeList2HTML()
					chgSpec['pidx'] = po.name
				newMove.save()
				newidx = newMove.idx
				newIDTbl[tmpidx] = newidx
				chgSpec['idx'] = newidx
			elif chgSpec['chgType'] == 'chg':
				mo = Movement.objects.get(idx=chgSpec['idx'])
				mo.name = moveName
				mo.save()
				
			# NB: mesoSys.name changed immediately in previewMoveEdits()

		except Exception as e:
			infoStr = 'user=%s applyMoveEdits EXCEPTION %s "%s"' % (userName,e,chgSpec)
			print(infoStr)
			logger.info(infoStr)
			sh_tHappened = True

	if sh_tHappened:
		errMsg = 'applyMoveEdits: %s MesoSystem sh_tHappened?!' % (mesoSysPK)
		return render(request, 'moveGen/err.html', {'errMsg': errMsg, 'except': '(no exception)'})
	else:
		if len(newIDTbl) > 0:
			# NB: replace temporary negative indices and pidx with new ones
			newMoveDict = updateIdx(editMoveDict,newIDTbl)
			mesoSys.moveDict = newMoveDict
			
		mesoSys.movesCommited = True
		mesoSys.save()
		
		infoStr = 'user=%s applyMoveEdits "%s"' % (userName,chg2apply)
		print(infoStr)
		logger.info(infoStr)
			
		sysqs = MesoSystem.objects.all()
		sysList = list(sysqs)
		
		context = {'sysList': sysList}
		
		return render(request, 'moveGen/bldMesoSys.html', context)

