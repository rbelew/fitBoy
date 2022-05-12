from django.contrib import admin


from django.contrib.postgres.fields import JSONField
from jsoneditor.forms import JSONEditor

from .models import *

# from .forms import MesoForm

admin.site.register(Client)
admin.site.register(Coach)
# admin.site.register(Schedule)
admin.site.register(Workout)
admin.site.register(WOSEval)

class CardioAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField:{ 'widget':JSONEditor },
    }
admin.site.register(CardioPattern, CardioAdmin)

# class MesoAdmin(admin.ModelAdmin):
# 	form = MesoForm
# 	
# admin.site.register(MesoCycle, MesoAdmin)

class MovementAdmin(admin.ModelAdmin):
	list_filter = ['mtype']
admin.site.register(Movement, MovementAdmin)

class MoveSeqAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField:{ 'widget':JSONEditor },
    }
admin.site.register(MoveSeq, MoveSeqAdmin)

class SchedAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField:{ 'widget':JSONEditor },
    }
admin.site.register(Schedule, SchedAdmin)

class MesoSystemAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField:{ 'widget':JSONEditor },
    }
admin.site.register(MesoSystem, MesoSystemAdmin)
