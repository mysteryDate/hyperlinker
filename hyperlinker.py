#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import re
from bs4 import BeautifulSoup
import Levenshtein
import unicodedata
import pdb

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]
# print("Which File: ")
# inFilePath = str(raw_input())
inFilePath = "input.txt"
outFilePath = inFilePath.rpartition('.')[0] + "_HYPERLINKED.txt"

textFile = open(inFilePath, "U")
output = open(outFilePath, "w")
fileData = textFile.readlines()
textFile.close()
businesses = []

for line in fileData:
	businesses.append({'name': unicode(line.rstrip(' \n'), 'utf-8')})
	# pdb.set_trace()


# for b in businesses:
# 	print "Name: " + str(b['name'])
# 	url = "https://www.google.ca/search?q=" + b['name'].replace(' ', '+').lower() + "+montreal"
# 	soup = BeautifulSoup(opener.open(url).read())
# 	# b['phone numbers'] = soup.find_all(text=re.compile("^(?:\([2-9]\d{2}\)\ ?|[2-9]\d{2}(?:\-?|\ ?))[2-9]\d{2}[- ]?\d{4}$"))
# 	links = soup.find_all('cite')
# 	a = soup.find_all('a')
# 	fbstr = ''
# 	for link in a:
# 		match = re.search("facebook", str(link['href']))
# 		if match:
# 			fbstr = str((link['href']))
# 			break
# 	b['facebook'] = fbstr
# 	b['facebook'] = fbstr.partition('&')[0]
# 	b['facebook'] = b['facebook'].partition('=')[2]
# 	print "Facebook: " + b['facebook']

def removeSkipWords(words):
	skipWords = ['au', 'le', 'de', 'the']
	for w in words:
		for s in skipWords:
			if w.lower() == s:
				words.remove(w)
	return words


def findMatchScore(searchName, foundName) :
	bigR = 0
	inputWords = searchName.replace(':', ' ').split(' ')
	foundWords = foundName.replace(':', ' ').split(' ')
	inputWords = removeSkipWords(inputWords)
	foundWords = removeSkipWords(foundWords)
	for iWord in inputWords:
		maxRatio = 0
		for fWord in foundWords:
			r = Levenshtein.ratio(iWord.lower().replace("/'s", ''), fWord.lower().replace("/'s", ''))
			if r > maxRatio:
				maxRatio = r
		bigR += maxRatio
	return bigR / len(inputWords)

# search yelp
for b in businesses:
	print "Name: " + b['name']
	name = unicodedata.normalize('NFKD', b['name']).encode('ascii','ignore')
	# pdb.set_trace()
	url = "https://www.yelp.com/search?find_desc=" + name.replace(' ', '+').lower() + "&find_loc=Montreal"
	soup = BeautifulSoup(opener.open(url).read())
	a = soup.find('a', class_="biz-name")
	bizname = str(a['href']).partition('#')[0]
	newurl = "https://www.yelp.com" + bizname
	soup = BeautifulSoup(opener.open(newurl).read())
	foundName = soup.find('h1', class_="biz-page-title").getText().strip(' \n').rstrip(' \n')
	foundName = unicodedata.normalize('NFKD', foundName).encode('ascii','ignore')
	if findMatchScore(name, foundName) > 0.75:
		website = soup.find('div', class_="biz-website")
		if website:
			b['website'] = website.find('a').getText().strip(' \n').rstrip(' \n')
			print b['website']
		phone = soup.find('span', class_="biz-phone	")
		if phone:
			b['phone number'] = phone.getText().strip(' \n').rstrip(' \n')
			print b['phone number']
		address = soup.find('address')
		span = address.find_all('span')
		b['address'] = {}
		for s in span:
			field = s['itemprop']
			b['address'][field] = s.getText()
		print b['address']['streetAddress']
		print b['address']['addressLocality'] + ', ' + b['address']['addressRegion']
		print b['address']['postalCode']
		print '\n'
	else:
		print 'Not found on yelp'


