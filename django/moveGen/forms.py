'''
Created on Jul 6, 2017

@author: rik
'''

from django import forms
from .models import *

# from django_select2.forms import Select2MultipleWidget, ModelSelect2Widget
#
# class SelectReqMove(ModelSelect2Widget):
#     search_fields = [
#         'mtype__icontains',
#     ]


class PickMeso(forms.Form):

	# NB initializing dynamic choices
	# https://stackoverflow.com/questions/3419997/creating-a-dynamic-choice-field
	def __init__(self, *args, **kwargs):
		
		super(PickMeso, self).__init__(*args, **kwargs)
		
		qs = MesoCycle2.objects.all()
		meso_choices = [(m.pk,m.name) for m in qs]
		self.fields['mesoName'] = forms.ChoiceField(choices=meso_choices)
	
	def __unicode__(self):
		return '%s' % (self.meso)



# class MesoForm(forms.ModelForm):
# 
# 	class Meta:
# 		model = MesoCycle
# 		fields = ['name','desc', 
# 					'nweek', 'nsessionWeek', 
# 				  'moveSeq','cardioPattern',
# 				  ]
# 
# 	class Media:
# 		# The keys in the dictionary are the output media types. These are the same types accepted by CSS files in media declarations: ‘all’, ‘aural’, ‘braille’, ‘embossed’, ‘handheld’, ‘print’, ‘projection’, ‘screen’, ‘tty’ and ‘tv’. 
# 		css = { 'all': ('pretty.css',) }
# 		js = ('animations.js', 'actions.js')
		

class NameSchedForm(forms.Form):
	def __init__(self, *args, **kwargs):

		super(NameSchedForm, self).__init__(*args, **kwargs)
		
		self.fields['schedName'] = forms.CharField(label='Schedule name', max_length=20)

class UnifSchedForm(forms.Form):
	def __init__(self, *args, **kwargs):

		super(UnifSchedForm, self).__init__(*args, **kwargs)
		
		self.fields['unifName'] = forms.CharField(label='Unified schedule name', max_length=20)

	# https://stackoverflow.com/a/2569784/1079688
# 	def _media(self):
# 		js = ("js/jquery.min.js", "js/select2/")
# 
# 		return forms.Media(js=js)
# 
# 	media = property(_media)
