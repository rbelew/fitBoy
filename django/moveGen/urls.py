'''
Created on Jul 2, 2017

@author: rik
''' 


from django.conf.urls import url,include

from django.contrib.auth import views as auth_views

from django.views.generic import TemplateView

from .forms import PickMeso
from .models import *
from .views import  *

# from .forms import MesoForm

urlpatterns = [
	
	# url(r'^ratings/', include('star_ratings.urls', namespace='ratings', app_name='ratings')),
	# (r'^ratings/', include('ratings.urls')),
	
	url(r'^login/$', auth_views.login, name='login'),
	url(r'^logout$', auth_views.logout, {'next_page':'index'}, name='logout',),

	# url(r'^select2/', include('django_select2.urls')),

    url(r'^$', toc, name='index'),

	url(r'^need2login/.*$', need2login, name='need2login'),

	url(r'^bldMesoSys/$', bldMesoSys, name='bldMesoSystem'),
	url(r'^commitMoves/(?P<mesoSysPK>.+)/$', applyMoveEdits, name='commitMoves'),
	url(r'^cloneMesoSys/(?P<mesoSysPK>.+)/$', cloneMesoSys, name='cloneMesoSys'),
	url(r'^deleteMesoSys/(?P<mesoSysPK>.+)/$', deleteMesoSys, name='deleteMesoSys'),
	
	url(r'^editMoves/(?P<mesoSysPK>.+)/$', editMoves, name='editMoves'),

	url(r'^previewMoveEdits/(?P<mesoSysPK>.+)/$', previewMoveEdits, name='previewMoveEdits'),
	url(r'^applyMoveEdits/(?P<mesoSysPK>.+)/$', applyMoveEdits, name='applyMoveEdits'),

	url(r'^toc/$', toc, name='toc'),

	url(r'^createCohortMeso/(?P<mesoSysPK>.+)/$', createCohortMeso, name='createCohortMeso'),
	url(r'^createIndivMeso/(?P<mesoSysPK>.+)/$', createIndivMeso, name='createIndivMeso'),
	url(r'^selectMeso/$', selectMeso, name='selectMeso'),
	url(r'^pprintMeso/(?P<meso2PK>.+)/$', pprintMeso, name='pprintMeso'),

	url(r'^saveMeso/$', saveMeso, name='saveMeso'),
	
	url(r'^bldNMWOS/(?P<meso2PK>.+)/(?P<schedName>.+)/$', bldNMWOS, name='bldNMWOS'),
	url(r'^primarySched/(?P<sched1pk>.+)/$', primaryNMSched, name='primarySched'),
	url(r'^primaryNMSched/(?P<sched1pk>.+)/$', primaryNMSched, name='primarySched'),
	url(r'^unifiedSched/(?P<sched1Idx>.+)_(?P<sched2Idx>.+)/$', unifiedSched, name='unified'),
	url(r'^allWOS/(?P<sched1Idx>.+)_(?P<sched2Idx>.+)/$', allWOS, name='allWOS'),
	url(r'^allWOS/(?P<sched1Idx>.+)/$', allWOS, name='allWOS_indiv'),
	url(r'^showSchedDist/(?P<sched1Idx>.+)/$', showSchedDist, name='showSchedDist'),

	url(r'^showWOS/(?P<wosIdx>.+)/$', showWOS, name='showWOS'),

	url(r'^deleteSched/(?P<pk>.+)/$', SchedDelete.as_view(), name='deleteSched'),

	url(r'^drawWOS/(?P<schedIdx>.+)_(?P<week>.+)_(?P<dayStr>.+)$', drawWOS),
	url(r'^saveWOS$', saveWOS),
	url(r'^evalWOSconfirm', TemplateView.as_view(template_name="moveGen/evalWOSconfirm.html")),

	url(r'^assess/(?P<clientIdx>.+)/$', clientAssess , name='clientAssess'),

]

# https://stackoverflow.com/a/6792076/1079688
# execute code in the top-level urls.py. That module is imported and executed once.
# 
# print('moveGen.urls: one-time inits')

# qs = MesoCycle.objects.all()
# ql = list(qs)
# PickMeso.choiceList = [(m.name,m.name) for m in ql]
# print ('moveGen.urls: PickMeso.choiceList=%s' % (PickMeso.choiceList))