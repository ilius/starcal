#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pre remove script

pkgName = 'starcal3'
import os


lines = open('/etc/passwd').read().split('\n')
for line in lines:
  if line=='':
	continue
  line = line.replace(',' ,'')
  parts = line.split(':')
  home = parts[5]
  try:
	os.remove('%s/Desktop/%s.desktop'%(home, pkgName))
  except:
	continue
  print('Removing x-desktop file from %s\'s Desktop'%parts[0])

