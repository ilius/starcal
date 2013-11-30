#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# post remove script for starcal2

pkgName = 'starcal2'
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

