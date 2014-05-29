#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import re
import pdb
inFilePath = "justaddresses.txt"
textFile = open(inFilePath, "U")
fileData = textFile.readlines()
textFile.close()

re.UNICODE

# r = re.compile("\A\d{1,5}[,]{0,1}[ ]{0,1}[\w \.'-]*", re.UNICODE)
r = re.compile("[A-Za-z]", re.UNICODE)
streetAdresses = []

for line in fileData:
	secs = line.split(',')
	# print secs
	# pdb.set_trace()
	m = r.search(secs[0])
	s = ""
	if m:
		s = secs[0]
	else:
		s = secs[0] + secs[1]
	streetAdresses.append(s)

addresses = []
r = re.compile("\A\d*")
for i in range(0, len(streetAdresses)):
	entry = {}
	entry['original'] = streetAdresses[i]
	dig = r.findall(streetAdresses[i])
	if dig:
		entry['number'] = dig[0]
		s = streetAdresses[i].lstrip(dig[0])
		entry['street'] = s
	addresses.append(entry)

print addresses


# pdb.set_trace()
# 
# p = r.findall(fileData[70])
# s = unicode(p[0], 'utf-8')
# print p
# p = r.findall(fileData[71])
# print p