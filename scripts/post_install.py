#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# post install script
import os, shutil

pkgName = 'starcal3'




"""
from gi.repository import Gtk as gtk
d = gtk.Dialog()
okB = d.add_button(gtk.STOCK_OK, 1)
okB.connect('clicked', lambda obj: d.hide())
pack(d.vbox, gtk.Label('StarCalendar post-install configuration'))
d.set_title('%s postinst'%pkgName)


check3 = gtk.CheckButton('Copy shortcut(x-desktop) file to Desktop')
check3.set_active(True)
pack(d.vbox, check3)

d.vbox.show_all()
d.set_keep_above(True)
d.run()

if check3.get_active():"""

lines = open('/etc/passwd').read().split('\n')
for line in lines:
	if line=='':
	  continue
	line = line.replace(',' ,'')
	parts = line.split(':')
	uid = int(parts[2])
	username = parts[0]
	if uid<1000:
	  continue
	if username=='nobody':
	  continue
	gid = int(parts[3])
	home = parts[5]
	target = '%s/Desktop/%s.desktop'%(home, pkgName)
	try:
	  shutil.copy('/usr/share/applications/%s.desktop'%pkgName, target)
	except:
	  continue
	print('Copying x-desktop file to %s\'s Desktop'%username)
	os.chown(target, uid, gid)


