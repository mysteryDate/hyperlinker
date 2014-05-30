#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import re
from bs4 import BeautifulSoup
import Levenshtein
import unicodedata
import codecs
import pdb

#for pages with javascript
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtWebKit import *
import sys

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]

inFilePath = "may_17_input.txt"
outFilePath = inFilePath.rpartition('.')[0] + "_TWITTERS.txt"

textFile = open(inFilePath, "U")
output = codecs.open(outFilePath, "w", 'utf-8')
fileData = textFile.readlines()
textFile.close()
businesses = []

for line in fileData:
	businesses.append({'searchName': unicode(line.rstrip(' \n'), 'utf-8')})

def searchTwitter(business):
	name = unicodedata.normalize('NFKD', business['searchName']).encode('ascii','ignore')
	url = "https://twitter.com/search?q="+name.replace(' ', '%20')+"%20montreal&mode=users"
	soup = BeautifulSoup(opener.open(url).read())
	a = soup.find('a', 'js-user-profile-link')
	if a:
		link = a['href']
		if link:
			business['twitter'] = "twitter.com" + link

for b in businesses:
	print "Search: " + b['searchName']
	b['twitter'] = ''
	output.write(b['searchName']+'\n')
	searchTwitter(b)
	if b['twitter']:
		print "twitter: " + b['twitter']
		output.write(b['twitter'] + '\n')
	output.write('\n')

output.close()
