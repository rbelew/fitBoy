from __future__ import unicode_literals

from django.utils.encoding import python_2_unicode_compatible

from django.db import models

from django.contrib.postgres.fields import JSONField

# from django.contrib.contenttypes.fields import GenericRelation
# from star_ratings.models import Rating

import json

MOVE_TYPES = (('Measure', 'Measure'), 
				('Accessory', 'Accessory'), 
				('Exercise', 'Exercise'), 
				)

MoveDepth2Type = {1: 'Measure', 2: 'Accessory', 3: 'Exercise'}

SCHEDULE_TYPES = (('Primary','Primary'),('Secondary','Secondary'))

@python_2_unicode_compatible
class Assessment(models.Model):
	idx = models.AutoField(primary_key=True)
	name = models.CharField(max_length=50)
	move = models.ForeignKey('movement',on_delete=models.CASCADE)

	def __str__(self):
		return '%s' % (self.name)

@python_2_unicode_compatible
class CardioPattern(models.Model):
	''' list ala ['PhCr','PhCr','PhCr','Gly','Gly','Gly','Endur']'
	'''
	idx = models.AutoField(primary_key=True)
	name = models.CharField(max_length=50)
	#2d: week x sessions / week
	# NB: integers are Movement pk ids!
	# schedule = ArrayField(ArrayField(models.IntegerField()),null=True,blank=True)
	schedule = JSONField(default={})

	def __str__(self):
		return '%s' % (self.name)

@python_2_unicode_compatible
class Client(models.Model):
	idx = models.AutoField(primary_key=True)
	fname = models.CharField(max_length=50)
	lname = models.CharField(max_length=50)

	def __str__(self):
		return '%s %s' % (self.fname,self.lname)

@python_2_unicode_compatible
class Coach(models.Model):
	idx = models.AutoField(primary_key=True)
	fname = models.CharField(max_length=50)
	lname = models.CharField(max_length=50)

	def __str__(self):
		return '%s %s' % (self.fname,self.lname)

# @python_2_unicode_compatible
# class MesoCycle(models.Model):
# 	
# 	idx = models.AutoField(primary_key=True)
# 	name = models.CharField(max_length=50)
# 	desc = models.CharField(max_length=200,null=True,blank=True)
# 	cdate = models.DateTimeField(auto_now_add=True,null=True,blank=True)
# 	
# 	nweek = models.IntegerField()
# 	nsessionWeek = models.IntegerField()
# 	assessWeek = models.IntegerField()
# 
# 	# Array of Integers for PK's is fragile
# 	# requiredMeasure = ArrayField(models.IntegerField(blank=True, choices=[]),
# 	# 								 default=list, blank=True)
# 	# 2do UGGH!
# 	reqMeas1 = models.ForeignKey('movement',related_name='req1',null=True,blank=True,default=None,on_delete=models.CASCADE)
# 	reqMeas2 = models.ForeignKey('movement',related_name='req2',null=True,blank=True,default=None,on_delete=models.CASCADE)
# 	reqMeas3 = models.ForeignKey('movement',related_name='req3',null=True,blank=True,default=None,on_delete=models.CASCADE)
# 	reqMeas4 = models.ForeignKey('movement',related_name='req4',null=True,blank=True,default=None,on_delete=models.CASCADE)
# 	reqMeas5 = models.ForeignKey('movement',related_name='req5',null=True,blank=True,default=None,on_delete=models.CASCADE)
# 	reqMeas6 = models.ForeignKey('movement',related_name='req6',null=True,blank=True,default=None,on_delete=models.CASCADE)
# 		
# 	moveSeq = models.ForeignKey('moveseq',null=True,on_delete=models.CASCADE)
# 	cardioPattern = models.ForeignKey('cardiopattern',on_delete=models.CASCADE)
# 	
# 	def __str__(self):
# 		return 'meso-%s-%s' % (self.name,self.idx)

@python_2_unicode_compatible
class MesoCycle2(models.Model):
	'''180304: make moveSeq a JSON dict, including cardio
		supporting both cohort & indiv mesos
	'''
	
	MesoAudiences = ( ('cohort', 'Cohort'), ('indiv', 'Individual') )
	
	idx = models.AutoField(primary_key=True)
	name = models.CharField(max_length=50)
	desc = models.CharField(max_length=200,null=True,blank=True)
	cdate = models.DateTimeField(auto_now_add=True,null=True,blank=True)
	author = models.CharField(max_length=20, null=True,blank=True)
	
	system = models.ForeignKey('mesosystem',null=True,blank=True,on_delete=models.PROTECT); 

	audience = models.CharField(max_length=20,choices=MesoAudiences, default='cohort',null=True,blank=True)
	
	# for audience=cohort, 
	nweek = models.IntegerField(null=True,blank=True)
	nsessionWeek = models.IntegerField(null=True,blank=True)
	# for audience=indiv, 
	totSession = models.IntegerField(null=True,blank=True)
	
	# ASSUME assessment is LAST week (for cohort) or last session (indiv)

	# weekIdx -> sessionIdx -> [reqMeas1,reqMeas2]
	# {"0":{"0":["Split Squat","OPEN"],"1":["TB Deadlift","Assault Bike"],"2":["Turkish Get-Up","OPEN"]},
	#  "1":{"0":["TB Deadlift","Assault Bike"],"1":["Split Squat","Push-Up"],"2":["Split Squat","OPEN"]}}	
	moveSeq = JSONField(default={})
	
	# includeQual: Qualities to be included in OPEN scheduling, even if not mentioned in moveSeq
	includeQual = JSONField(default=[])
	
	# excludeAccry: accessorioes to be excluded from workouts
	excludeAccry = JSONField(default=[])
	
	def __str__(self):
		return 'meso-%s-%s' % (self.name,self.idx)
	
	def assessNow(self,wi,si):
		'''true iff week/session is for assessment
		'''
	
		if self.audience=='cohort':
			return wi == self.nweek - 1
		elif self.audience=='indiv':
			return si == self.totSession - 1;

@python_2_unicode_compatible 
class MesoSystem(models.Model):
	'''A collection of related Movements
	'''
	idx = models.AutoField(primary_key=True)
	name = models.CharField(max_length=120, null=True,blank=True)
	cdate = models.DateTimeField(auto_now_add=True,null=True,blank=True)
	author = models.CharField(max_length=20, null=True,blank=True)

	moveDict = JSONField(default={})
	# moveDict JSON format:
		
	# {"name":"Movements","idx":0,"children":[
	# 	{"mtype":"Measure","name":"Cardio Power // Assault Bike","idx":121,"children":[
	# 		{"mtype":"Accessory","name":"Endurance","idx":127,"children":[
	# 			{"mtype":"Exercise","name":"--/keep moving workout/--","idx":150,"children":[]},
	# 			{"mtype":"Exercise","name":"Erg 2+ minute intervals","idx":149,"children":[]},

	# NB: idx can be random NEGATIVE number only in UNCOMMITTED MS's
	#     also should not be any "pidx" 
	#		see updateIdx()
		
	
	movesCommited = models.BooleanField(default=False)


@python_2_unicode_compatible
class MoveSeq(models.Model):
	'''a mapping from all Measure to a list specifying the order in which other Measure moves are to be executed
	'''
	idx = models.AutoField(primary_key=True)
	name = models.CharField(max_length=50)
	json = JSONField(default={})
	
	def __str__(self):
		return '%s' % (self.name)
	
	def repr(self):
		s = self.name + '\n'
		tbl = self.json
		for m1,m2List in tbl.items():
			s += '%s:\t%s\n' % (m1,m2List)
		return s
		

@python_2_unicode_compatible
class Movement(models.Model):
	idx = models.AutoField(primary_key=True)
	name = models.CharField(max_length=50,db_index=True)
	abbrev = models.CharField(max_length=10, null=True,blank=True)
	# NB: mtype required
	# mtype \in ('Measure', 'Accessory', 'Exercise')
	mtype =  models.CharField(max_length=50, choices=MOVE_TYPES,default='Exercise')
	task = models.CharField(max_length=50,null=True,blank=True)
	parent = models.ForeignKey('self',null=True,on_delete=models.CASCADE)
	cardio = models.BooleanField(default=False)
	
	# assess = models.ForeignKey('self',related_name='move_assess',null=True,on_delete=models.CASCADE)
	# parent = models.ForeignKey('self',related_name='move_parent',null=True,on_delete=models.CASCADE)
	# kids = models.ForeignKey('self',related_name='move_kids',null=True,on_delete=models.CASCADE)

	def __str__(self):
		return '%s' % (self.name)

	# 180626: 2do? Make Movement uniqueness dependent on MesoSystem
	#
	# cf. https://stackoverflow.com/questions/8950010/django-model-auto-increment-primary-key-based-on-foreign-key
	
	#     key = models.PositiveIntegerField()
	#     fk = models.ForeignKey(ModelB)
	# 
	#     def Meta(self):
	#         unique_together = ("key", "fk")
	# 
	#     def save(self, *args, **kwargs):
	#         key = cal_key(self.fk)
	#         self.key = key
	#         super(ModelA, self).save(*args, **kwargs)
        
# @python_2_unicode_compatible
# class Program(models.Model):
# 	idx = models.AutoField(primary_key=True)
# 
# 	def __str__(self):
# 		return 'prog-%s' % (self.idx)

@python_2_unicode_compatible 
class Schedule(models.Model):
	'''A dated MesoCycle of Workouts for a client
	'''
	idx = models.AutoField(primary_key=True)
	name = models.CharField(max_length=20, null=True,blank=True)
	mesoVersion = models.CharField(max_length=2, null=True,blank=True) # v1, v2
	# meso = models.ForeignKey('mesocycle',null=True,blank=True,on_delete=models.CASCADE)
	meso2 = models.ForeignKey('mesocycle2',null=True,blank=True,on_delete=models.CASCADE)
	cdate = models.DateTimeField(auto_now_add=True,null=True,blank=True)
	stype = models.CharField(max_length=20, choices=SCHEDULE_TYPES,default='Primary')
	# primary only used in secondary schedules, to point to related primary schedule
	primary = models.ForeignKey('schedule',null=True,blank=True,default=None,on_delete=models.CASCADE)
	distribQual = models.FloatField(null=True,blank=True)
	# client = models.ForeignKey('client',on_delete=models.CASCADE)
	# beginDate = models.DateTimeField()
	
	# details: week -> day -> [ (mtype,move),... ]
	# NB: integers are Movement pk ids!
	details = JSONField(default={})
	
	

	def __str__(self):
		if self.mesoVersion == None:
			midx = self.meso.idx
		else:
			midx = self.meso2.idx
		if self.name == None:
			lbl = '%s-%s' % (self.idx, midx)
		else:
			lbl = '%s:%s-%s' % (self.name,self.idx, midx)
		return 'schedule-%s' % lbl


@python_2_unicode_compatible
class Workout(models.Model):
	'''A sequence of Movements to be performed during a single workout session
	'''
	idx = models.AutoField(primary_key=True)
	woName = models.CharField(max_length=40, null=True,blank=True)
	createDate = models.DateTimeField(auto_now_add=True,null=True,blank=True)
	author = models.CharField(max_length=20, null=True,blank=True)
	meso2 = models.ForeignKey('mesocycle2',null=True,blank=True,on_delete=models.CASCADE)
	sched = models.ForeignKey('schedule',null=True,blank=True,on_delete=models.CASCADE)
	week = models.IntegerField(null=True,blank=True)
	# NB: day is indexed ACROSS BOTH primary and secondary schedules
	# cf. views.saveWOS()
	day = models.IntegerField(null=True,blank=True)
	
	#  [{"idx":955,"name":"Complex (BB, KB, bw)","nrep":1},
	schedList = JSONField(default={})

	def __str__(self):
		return 'workout-%s' % (self.idx)

@python_2_unicode_compatible
class WOSEval(models.Model):
	'''An assessment of how well the workout worked
	'''
	
	idx = models.AutoField(primary_key=True)
	workout = models.ForeignKey('workout',on_delete=models.CASCADE)
	eval = models.IntegerField()
	# 2do: ensure evaluator is COACH
	# evaluator = models.ForeignKey('coach',null=True,blank=True,on_delete=models.CASCADE)
	evaluator = models.CharField(max_length=10, null=True,blank=True)
	evalDate = models.DateTimeField(auto_now_add=True,null=True,blank=True)
	comments = models.CharField(max_length=200, null=True,blank=True)
	
# from ratings.handlers import ratings
# from ratings.forms import StarVoteForm
# ratings.register(Workout, score_range=(1, 5), form_class=StarVoteForm)



