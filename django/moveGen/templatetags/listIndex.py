'''
Created on Dec 14, 2017

@author: rik
'''

from django import template
register = template.Library()

@register.filter
def listIndex(List, i):
    return List[int(i)]
