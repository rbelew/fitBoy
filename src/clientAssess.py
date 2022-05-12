
import calendar
from collections import defaultdict
import csv 
from datetime import datetime,timedelta,date
import json
from numpy.dual import norm

AssessFields = ('Idx','First Name','Last Name','Measure Name','Measurement','Description','Benchmark','Result','Rx?','Notes','SetsXReps','PR','Record Date')

AssessFields1 = ('First Name', 'Last Name', 'Measure Name', 'Result', 'ResultUnits', 'Rx?', 'Notes', 'Sets', 'Reps', 'PR', 'PRUnits', 'Record Date')

class Client():
	NClients = 0
	
	def __init__(self,lname,fname):
		self.lname = lname
		self.fname = fname
		Client.NClients += 1
		self.idx = Client.NClients
		self.assess = defaultdict(list)
		
# def normZPData-OBS(inf,outf):
# 	'''handle missing tabs in ZP output(:
# 	180922: Give up; edit manually
# 	'''
# 	
# 	clientTbl = {}
# 	outs = open(outf,'w')
# 	nhdr = None
# 	# NB: zenplanner output more predictable via TSV
# 	reader = csv.reader(open(inf),delimiter='\t')
# 	for i,row in enumerate(reader):
# 		if i==0:
# 			hdr = row
# 			nhdr = len(row)
# 			outs.write(','.join(row) + '\n')
# 			continue
# 		nfld = len(row)
# 		if nfld == nhdr:
# 			outs.write(','.join(row) + '\n')
# 			continue
# 		
# 		# missing desc
# 		if row[4].strip() == 'Yes' or row[4].strip() == 'No':
# 			row.insert(4,' ')
		

DateFmt1 = '%m/%d/%y' # 10/09/17
DateFmt = '%b %d, %Y' # Sep 17, 2018

def splitResUnit(s):
	if s.find(' ') == -1:
		try:
			v = int(s.strip())
		except:
			return 0,None
		return v,None
	
	v,unit = s.split(' ')
	if v.find('.') == -1:
		v = int(v)
	else:
		v = int(float(v))
	return v,unit

def loadAssess(inf):
	
	clientTbl = {}
	nskip=0
	reader = csv.DictReader(open(inf))
	for i,entry in enumerate(reader):
			
		ckey = entry['Last Name'] + '_' + entry['First Name']
		if ckey not in clientTbl:
			client =  Client(entry['Last Name'],entry['First Name'])
		else:
			client = clientTbl[ckey]
			
		measure = entry['Measure Name']
		mdate = datetime.strptime(entry['Record Date'],DateFmt)
		
		res, unit = splitResUnit(entry['Result'])
		if unit == None:
			print('loadAssess: idx=%s %s No result units? %s' % (entry['Idx'], ckey, entry['Result']))
			
		setRepStr = entry['SetsXReps']
		if setRepStr.find('x') != -1:
			set,rep = setRepStr.split('x')
		else:
			set = rep = 0
		# NB: no need to strip off spaces!
		set = int(set)
		rep = int(rep)
		
		pr, prunit = splitResUnit(entry['PR'])
		result = {'r': res,
				 	'unit': unit,
				 	'set': set,
				 	'rep': rep,
				 	'date': mdate,
				 	'pr': pr,
				 	'prunit': prunit}
				
		client.assess[measure].append(result)
		clientTbl[ckey] = client
	return clientTbl

def rptClientTbl(clientTbl):
	allAssess = defaultdict(int) # measure -> freq
	allClient = list(clientTbl.keys())
	allClient.sort()
	for ckey in allClient:
		print(ckey)
		for measure in clientTbl[ckey].assess:
			allAssess[measure] += 1
			print('\t%s %d' % (measure,len(clientTbl[ckey].assess[measure])))
	print(allAssess)
	
def calcNorm(result):
	return result['r'] * result['set'] * result['rep']

def bldRadarJSON(clientTbl,outJSON,outCSV):
	'''produce JSON version of clientTbl as expected by bremer-radarChartD3.js
	'''

	# var data = [
	# 		  [//iPhone
	# 			{axis:"Battery Life",value:0.22},
	# 			{axis:"Brand",value:0.28},
	# 			# ...
	# 			],[//Samsung
	# 			{axis:"Battery Life",value:0.27},
	# 			# ...
	# 		  ]
	# 		];
	
	allCKey = list(clientTbl.keys())
	allCKey.sort()
	
	maxVal = {}
	for ckey in allCKey:
		client = clientTbl[ckey]
		for m in client.assess.keys():
			result = clientTbl[ckey].assess[m]
			val = calcNorm(result)
			if m not in maxVal or maxVal[m] < val:
				maxVal[m] = val

	allMeasure = list(maxVal.keys())
	allMeasure.sort()
	print('Max values')
	for m in allMeasure:
		print(m,maxVal[m])
	
	data = []
	for ckey in allCKey:
		clist = []
		for m in allMeasure:
			d = {}
			d['axis'] = m
			if m in clientTbl[ckey].assess:
				result = clientTbl[ckey].assess[m]
				val = calcNorm(result)
				norm = float(val) / maxVal[m] 
				d['value'] = norm
			else:
				d['value'] = 0.0 
			clist.append(d)
		data.append(clist)
			
	outs = open(outJSON,'w')
	json.dump(data,outs)
	outs.close()	
	
	outs = open(outCSV,'w')
	line = 'LName,Fname,Idx'
	for m in allMeasure:
		line += ',%s-raw,%s-norm' % (m,m)
	outs.write(line+'\n')
	for i,ckey in enumerate(allCKey):
		client = clientTbl[ckey]
		# NB: using the parallel indexing of allCKey and data list!
		line = '%s,%s,%d' % (client.lname,client.fname,i)
		for m in allMeasure:
			if m in clientTbl[ckey].assess:
				result = clientTbl[ckey].assess[m]
				val = calcNorm(result)
				norm = float(val) / maxVal[m]
				if result['pr']:
					val = -val
					norm = -norm
			else:
				val = 0.0
				norm = 0.0
			line += ',%d,%f' % (val,norm)
		outs.write(line+'\n')
	outs.close()

def bldMonthSumm(clientTbl,monthSummFile,currClientOnly=True):
	'''produce plottable monthly summ
	'''
	
	minMonth = 13
	maxMonth = 0
	allMeasureSet = set()
	for ckey in clientTbl:
		for meas in clientTbl[ckey].assess:
			allMeasureSet.add(meas)
			for res in clientTbl[ckey].assess[meas]:
				mon = res['date'].month
				if mon < minMonth:
					minMonth = mon
				if mon > maxMonth:
					maxMonth = mon
	allMeasure = list(allMeasureSet)
	allMeasure.sort()
	outs = open(monthSummFile,'w')

	for meas in allMeasure:	
		summTbl = defaultdict(lambda: defaultdict(int)) # client -> mon -> res	
		for ckey in clientTbl:
			if meas not in clientTbl[ckey].assess:
				continue
			for res in clientTbl[ckey].assess[meas]:
				mon = res['date'].month
				summTbl[ckey][mon] = res['r']
			# fill in any missing months
			for mon in range(minMonth,maxMonth+1):
				if mon not in summTbl[ckey]:
					summTbl[ckey][mon] = 0

		
		measClient = list(summTbl.keys())
		measClient.sort()
		
		outs.write('\n# %s\n' % (meas))
		outs.write('Client')
		for mon in range(minMonth,maxMonth+1):
			outs.write(',%s' % (calendar.month_abbr[mon]))
		outs.write('\n')

		for ckey in measClient:
			outs.write('%s' % ckey)
			for mon in range(minMonth,maxMonth+1):
				outs.write(',%d' % summTbl[ckey][mon])
			outs.write('\n')
	outs.close()
				
if __name__ == "__main__":
	dataDir = '/Data/whbFit/clientAssess/'
	assessFile = dataDir + 'assess_180922-edit.csv'
	
	clientTbl = loadAssess(assessFile)
	
	# rptClientTbl(clientTbl)
	
	monthSummFile = dataDir + 'assess_180922-monthSumm.csv'
	bldMonthSumm(clientTbl,monthSummFile)
	
# 	jsonfile = dataDir + 'tfa_assess_171030-radar.json'
# 	csvNormfile = dataDir + 'tfa_assess_171030-normed.csv'
# 	bldRadarJSON(clientTbl,jsonfile,csvNormfile)
		
