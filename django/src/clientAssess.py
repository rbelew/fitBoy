
from collections import defaultdict
import csv 
from datetime import datetime,timedelta,date
import json
from numpy.dual import norm

AssessFields = ('First Name', 'Last Name', 'Measure Name', 'Result', 'ResultUnits', 'Rx?', 'Notes', 'Sets', 'Reps', 'PR', 'PRUnits', 'Record Date')

class Client():
	NClients = 0
	
	def __init__(self,lname,fname):
		self.lname = lname
		self.fname = fname
		Client.NClients += 1
		self.idx = Client.NClients
		self.assess = {}
		
DateFmt = '%m/%d/%y' # 10/09/17
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
		r = 0 if entry['Result'] == '' else int(entry['Result'])
		set = 1 if entry['Sets'] == '' else int(entry['Sets'])
		rep = 1 if entry['Reps'] == '' else int(entry['Reps'])
		pr = 0 if entry['PR'] == '' else int(entry['PR'])
		result = {'r': r,
				 	'unit': entry['ResultUnits'],
				 	'set': set,
				 	'rep': rep,
				 	'date': mdate}
		result['pr'] = result['r'] == pr
		
		if measure in client.assess and client.assess[measure]['date']>=mdate:
			print('loadAssess: skipping older assess',ckey,measure,mdate,client.assess[measure]['date'])
			nskip += 1
			continue
		
		client.assess[measure] = result
		clientTbl[ckey] = client
	return clientTbl

def rptClientTbl(clientTbl):
	for ckey in clientTbl.keys():
		print(ckey,clientTbl[ckey].assess.keys())

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
			
if __name__ == "__main__":
	dataDir = '/Data/whbFit/fitAlchem/'
	assessFile = dataDir + 'tfa_assess_171030.csv'
	clientTbl = loadAssess(assessFile)
	
	jsonfile = dataDir + 'tfa_assess_171030-radar.json'
	csvNormfile = dataDir + 'tfa_assess_171030-normed.csv'
	bldRadarJSON(clientTbl,jsonfile,csvNormfile)
		
