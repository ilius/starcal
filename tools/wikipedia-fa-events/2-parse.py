#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os, re, json
from os.path import join

faDigs = ('۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹', '٫')

ignoreCategories = ('تعطیلات', 'جستارهای وابسته', 'منابع')

getPrettyJson = lambda data: json.dumps(data, sort_keys=True, indent=4)

def numFaDecode(numFa):
	if isinstance(numFa, str):
		numFa = numFa.decode('utf8')
	numStr = ''
	for c in numFa:
		numStr += str(faDigs.index(c))
	return int(numStr)

def cleanRawText(text):
	text = text.strip()## .replace(']]', '').replace('[[', '')
	for part in re.findall('\[\[.*?\]\]', text):
		part2 = part.split('|')[-1]
		text = text.replace(part, part2)
	return text.replace('[[', '').replace(']]', '').replace("'''", '')\
			   .replace('٬ ', '، ')\
			   .replace('ي', 'ی')\
			   .replace('ك', 'ک')


def parseFile(fpath, month, day):
	#print(fpath, month, day)
	category = ''
	data = []
	for line in open(fpath).read().split('\n'):
		if line.startswith('== '):
			category = line[2:-2].strip()
			if category in ignoreCategories:
				category = ''
			continue
		if category and line.startswith('* '):
			try:
				yearFa = line.split('[[')[1].split(']]')[0]
				year = numFaDecode(yearFa)
			except:
				continue
			textStart = line.find('-')
			#print(textStart)
			if textStart<0:
				continue
			text = cleanRawText(line[textStart+1:])
			#print('text=%s'%text)
			data.append({
				'date': (year, month, day),
				'category': category,
				'text': text,
			})
	return data


def parseAllFiles(direc):
	data = []
	for monthFname in os.listdir(direc):
		if monthFname.endswith('~'):
			continue
		#try:
		month = int(monthFname)
		#except ValueError, e:
		#	continue
		mDirec = join(direc, monthFname)
		for dayFname in os.listdir(mDirec):
			if dayFname.endswith('~'):
				continue
			#try:
			day = int(dayFname)
			#except ValueError:
			#	continue
			data += parseFile(join(mDirec, dayFname), month, day)
	data.sort()
	return data

def writeToTabfile(data, fpath):
	lines = []
	for event in data:
		lines.append('%s\t%s\t%s'%(
			'%.4d/%.2d/%.2d'%tuple(event['date']),
			event['category'],
			event['text'],
		))
	open(fpath, 'w').write('\n'.join(lines))



if __name__=='__main__':
	from pprint import pprint
	data = parseAllFiles('wikipedia-fa-events')
	writeToTabfile(data, 'wikipedia-fa.tab')
	#print(getPrettyJson(data))
	#pprint(data)




