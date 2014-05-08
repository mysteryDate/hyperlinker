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
sites = ['facebook', 'yelp', 'yellowpages', 'urbanspoon', 'twitter']

for line in fileData:
	businesses.append({'searchName': unicode(line.rstrip(' \n'), 'utf-8')})
	# pdb.set_trace()

def removeSkipWords(words):
	skipWords = ['au', 'le', 'de', 'the']
	for w in words:
		for s in skipWords:
			if w.lower() == s:
				words.remove(w)
	return words


def findMatchScore(searchName, foundName) :
	if(type(searchName) is unicode):
		searchName = unicodedata.normalize('NFKD', searchName).encode('ascii','ignore')
	if(type(foundName) is unicode):
		foundName = unicodedata.normalize('NFKD', foundName).encode('ascii','ignore')
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

def searchYellowpages(business):
	url = business['yellowpages']
	pdb.set_trace()
	soup = BeautifulSoup(opener.open(url).read())
	if business['foundName'] == business['searchName']:
		business['foundName'] = soup.find('h1', itemprop="name").getText().strip(' \n').rstrip(' \n')
	if not business['address']:
		address = soup.find('address', itemprop="address")
		if address:
			business['address'] = address.getText().strip(' \n').rstrip(' \n')
	if not business['phone']:
		phone = soup.find('li', class_="phone")
		if phone:
			business['phone'] = phone.getText().strip(' \n').rstrip(' \n')
	if not business['website']:
		website = soup.find('li', class_="website")
		if website:
			a = website.find('a', itemprop="url")
			business['website'] = str(a['href']).partition("www.")[2].rstrip(' \n')

# search yelp
def searchYelp(business):
	if not business['yelp']:
		name = unicodedata.normalize('NFKD', business['searchName']).encode('ascii','ignore')
		url = "https://www.yelp.com/search?find_desc=" + name.replace(' ', '+').lower() + "&find_loc=Montreal"
		soup = BeautifulSoup(opener.open(url).read())
		a = soup.find('a', class_="biz-name")
		bizname = str(a['href']).partition('#')[0]
		newurl = "https://www.yelp.com" + bizname
		soup = BeautifulSoup(opener.open(newurl).read())
		foundName = soup.find('h1', class_="biz-page-title").getText().strip(' \n').rstrip(' \n')
		foundName = unicodedata.normalize('NFKD', foundName).encode('ascii','ignore')
		if findMatchScore(name, foundName) > 0.75:
			business['yelp'] = newurl
		else:
			print 'Not found on yelp\n'
			return
	else:
		newurl = business['yelp']
		soup = BeautifulSoup(opener.open(newurl).read())
	business['foundName'] = soup.find('h1', class_="biz-page-title").getText().strip(' \n').rstrip(' \n')
	website = soup.find('div', class_="biz-website")
	if website:
		business['website'] = website.find('a').getText().strip(' \n').rstrip(' \n')
	phone = soup.find('span', class_="biz-phone")
	if phone:
		business['phone'] = phone.getText().strip(' \n').rstrip(' \n')
	address = soup.find('address')
	if address:
		business['address'] = address.getText().strip(' \n').rstrip(' \n')

def searchFacebook(business):
	name = unicodedata.normalize('NFKD', business['searchName']).encode('ascii','ignore')
	url = "https://www.facebook.com/search/more/?q="+ name.replace(' ', '+').lower() +"%20montreal"
	soup = BeautifulSoup(opener.open(url).read())
	div = soup.find_all('div')
	return

def getLink(siteName, links):
	linkString = ''
	for l in links:
		match = re.search(siteName, str(l['href']))
		if match:
			linkString = str((l['href']))
			linkString = linkString.partition('&')[0]
			linkString = linkString.partition('=')[2]
			break
	return linkString

def searchGoogle(business):
	name = unicodedata.normalize('NFKD', business['searchName']).encode('ascii','ignore')
	url = "https://www.google.ca/search?q=" + name.replace(' ', '+').lower() + "+montreal"
	soup = BeautifulSoup(opener.open(url).read())
	spell = soup.find('a', class_="spell")
	if spell:
		actualName = spell['href'].partition('&')[0]
		business['foundName'] = unicode(actualName.partition('=')[2].replace('+', ' ').replace(" montreal", ''), 'utf-8')
	if not business['phone']:
		business['phone'] = soup.find(text=re.compile("^(?:\([2-9]\d{2}\)\ ?|[2-9]\d{2}(?:\-?|\ ?))[2-9]\d{2}[- ]?\d{4}$"))
	a = soup.find_all('a')
	for s in sites:
		business[s] = getLink(s, a)
		# print s + ': ' + business[s]
	# url = "https://www.google.ca/search?q=" + name.replace(' ', '+').lower() + "+montreal+twitter"


for b in businesses:
	print "Search: " + b['searchName']
	b['foundName'] = b['searchName']
	b['address'] = ''
	b['phone'] = ''
	b['website'] = ''
	for s in sites:
		b[s] = ''
	# google is definitely on to me, I should be careful
	searchGoogle(b)
	if b['foundName'] != b['searchName']:
		print "It's probably called: " + b['foundName']
	searchYelp(b)
	if not b['website'] or not b['address'] or not b['phone'] and b['yellowpages']:
		searchYellowpages(b)
	# Facebook requires login
	# if b['facebook'] != '':
	# 	if b['address'] == '':
	# 	searchFacebook(b) 
	print b['foundName']
	if findMatchScore(b['searchName'], b['foundName']) > 0.75:
		print "website: " + b['website']
		print "phone: " + b['phone']
		print "address: " + b['address']
		print "facebook" + b['facebook']
	else:
		print "probably not what you're looking for"
	print '\n'
	




