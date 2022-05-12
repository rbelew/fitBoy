''' modulo
Created on Jan 11 2018

@author: rik
'''

from django import template
register = template.Library()

@register.filter
def modulo(i, denom):
    return i % denom
