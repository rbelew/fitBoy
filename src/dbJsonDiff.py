''' dbJsonDiff: compare two django dumpdata json files

	compare all of (some) models' data rows in file1 file2 dumpdata lists
	
Created on Jan 12, 2019

@author: rik
'''

from collections import defaultdict
import json
import json_diff

def main():
	
	dataDir = '/Data/whbFit/fitAlchem/db-bak/'
	inf1 = dataDir + 'movegen_190111.json'
	inf2 = dataDir + 'movegen_190111-2.json'
	filterModels = ['admin','auth','sessions']
	
	olist1 = json.load(open(inf1))
	# objTbl1: model -> idx -> {}
	# objTbl1 = defaultdict(lambda: defaultdict( {} )) 
	objTbl1 = {} 
	for odict in olist1:
		m = odict['model']
		bits = m.split('.')
		if bits[0] in filterModels:
			continue
		mname = bits[1]
		if mname not in objTbl1:
			objTbl1[mname] = {}
		pk = odict['pk']
		objTbl1[mname][pk] = odict
		
	olist2 = json.load(open(inf2))
	objTbl2 = {} 
	for odict in olist2:
		m = odict['model']
		bits = m.split('.')
		if bits[0] in filterModels:
			continue
		mname = bits[1]
		if mname not in objTbl2:
			objTbl2[mname] = {}
		pk = odict['pk']
		objTbl2[mname][pk] = odict
		
		
	diff = json_diff.Comparator()
	diff.obj1 = objTbl1
	diff.obj2 = objTbl2
	
	diff_res = diff.compare_dicts()
	# outStr = str(json_diff.HTMLFormatter(diff_res))
	outStr = json.dumps(diff_res, indent=1)
	outf = dataDir + 'dataDumpDiff.json'
	outs = open(outf,'w')
	outs.write(outStr+'\n')
	outs.close()
	

if __name__ == '__main__':
	main()