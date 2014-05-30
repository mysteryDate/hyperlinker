#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import re
import pdb
inFilePath = "justaddresses.txt"
textFile = open(inFilePath, "U")
fileData = textFile.readlines()
textFile.close()

# r = re.compile("\A\d{1,5}[,]{0,1}[ ]{0,1}[\w \.'-]*", re.UNICODE)
numRegex = re.compile("\A\d{1,5}[A-Z]{1}[ ,]|\A\d{1,5}", re.UNICODE)
addresses = []

for line in fileData:
	address = {}
	s = line
	num = numRegex.findall(line)[0]
	if num:
		num = num.rstrip(' ,')
		s = s.replace(num, '').lstrip(' ,')
		s = s.lstrip()
		address['number'] = num
		address['street'] = s.partition(',')[0].rstrip(' \n').lower()
		addresses.append(address)
	else:
		print "problem with ", line

roadTrans = {}
roadTrans['abbr'] = {'boul': 'boulevard', 'blvd': 'boulevard', 'ch': 'chemin', 'av': 'avenue', 'av': 'avenue', 'o': 'ouest', 'e': 'est', 'n': 'nord', 's': 'sud'}
# key = french, value = english
roadTrans['type'] = {'rue': 'street', 'avenue': 'avenue', 'boulevard': 'boulevard', 'chemin': 'road'}
roadTrans['direction'] = {'ouest': 'west', 'nord': 'north', 'sud': 'south', 'est': 'east'}

for i, ad in enumerate(addresses):
	street = ad['street'].split()
	# remove abbreviation
	roadType = ''
	roadDirection = ''
	for j, word in enumerate(street):
		if word in roadTrans['abbr']:
			street[j] = roadTrans['abbr'][word]
	for word in list(street):
		if word in roadTrans['type']:
			street.remove(word)
			roadType = roadTrans['type'][word]
		if word in roadTrans['direction']:
			street.remove(word)
			roadDirection = roadTrans['direction'][word]
	if roadType:
		street.append(roadType)
	if roadDirection:
		street.append(roadDirection)
	# capitalize
	for i in range(0, len(street)):
		hyphens = street[i].split('-')
		final = []
		for w in hyphens:
			final.append(w.capitalize())
		street[i] = '-'.join(final)
	ad['street'] = ' '.join(street).rstrip()
	print ad['number'] + ' ' + ad['street']


