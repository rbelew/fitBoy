''' blfColors:  create RANDOM colormap for <= 20 colors
Created on Jan 14, 2019

@author: rik
'''

import colorsys
import random
# https://martin.ankerl.com/2009/12/09/how-to-create-random-colors-programmatically/
# 
# equally bright and colorful colors by using a fixed value for
# saturation and value, and just modifying the hue

Golden_ratio_conjugate = 0.618033988749895

def nextFiboRGB(h):
	h += Golden_ratio_conjugate
	h %= 1
	rgb = colorsys.hsv_to_rgb(h, ConstantSaturation, ConstantValue)
	return rgb,h
	
def main():
	
	ConstantSaturation=0.3 
	ConstantValue=0.99
	
	MaxNColor = 20
	colorVec = []
	
	h = random.random()
	for i in range(MaxNColor):
		rgb,newh = nextFiboRGB(h)
		colorVec.append(rgb)
		h = newh
	
	for i in range(MaxNColor):
		print(i,colorVec[i])
	
if __name__ == '__main__':
	pass