import math
from math import pi

earthR = 6370

sind = lambda x: math.sin(pi/180.0*x)
cosd = lambda x: math.cos(pi/180.0*x)
#tand = lambda x: math.tan(pi/180.0*x)
#asind = lambda x: math.asin(x)*180.0/pi
#acosd = lambda x: math.acos(x)*180.0/pi
#atand = lambda x: math.atan(x)*180.0/pi
#loc2hor = lambda z, delta, lat: acosd((cosd(z)-sind(delta)*sind(lat))/cosd(delta)/cosd(lat))/15.0

def earthDistance(lat1, lng1, lat2, lng2):
	#if lat1==lat2 and lng1==lng2:
	#	return 0
	dx = lng2 - lng1
	if dx<0:
		dx += 360
	if dx>180:
		dx = 360-dx
	####
	dy = lat2 - lat1
	if dy<0:
		dy += 360
	if dy>180:
		dy = 360-dy
	####
	deg = math.acos(cosd(dx)*cosd(dy))
	if deg > pi:
		deg = 2*pi - deg
	return deg*earthR
	#return ang*180/pi


