#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import re
from bs4 import BeautifulSoup
import Levenshtein
import unicodedata
import codecs
import pdb

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]
# print("Which File: ")
# inFilePath = str(raw_input())
inFilePath = "input.txt"
outFilePath = inFilePath.rpartition('.')[0] + "_HYPERLINKED.txt"

textFile = open(inFilePath, "U")
output = codecs.open(outFilePath, "w", 'utf-8')
fileData = textFile.readlines()
textFile.close()
businesses = []
sites = ['facebook', 'yelp', 'yellowpages', 'urbanspoon', 'twitter']

for line in fileData:
	businesses.append({'searchName': unicode(line.rstrip(' \n'), 'utf-8')})

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
	bigR2 = 0 # if the input has MORE words that the solution (rare)
	for fWord in foundWords:
		maxRatio = 0
		for iWord in inputWords:
			r = Levenshtein.ratio(iWord.lower().replace("/'s", ''), fWord.lower().replace("/'s", ''))
			if r > maxRatio:
				maxRatio = r
		bigR2 += maxRatio
	bigR /= len(inputWords)
	bigR2 /= len(foundWords)
	return max(bigR, bigR2)

def searchYellowpages(business):
	url = business['yellowpages']
	soup = BeautifulSoup(opener.open(url).read())
	if business['foundName'] == business['searchName']:
		header = soup.find('h1', itemprop="name")
		if header:
			business['foundName'] = header.getText().strip(' \n').rstrip(' \n')
	if not business['address']:
		address = soup.find('address', itemprop="address")
		if address:
			span = address.find('span', itemprop="streetAddress")
			if span:
				business['address'] = span.getText().strip(' \n').rstrip(' \n')
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
		if a:
			bizname = str(a['href']).partition('#')[0]
			newurl = "https://www.yelp.com" + bizname
			soup = BeautifulSoup(opener.open(newurl).read())
			titleName = soup.find('h1', class_="biz-page-title")
			if titleName:
				foundName = titleName.getText().strip(' \n').rstrip(' \n')
				foundName = unicodedata.normalize('NFKD', foundName).encode('ascii','ignore')
				if findMatchScore(name, foundName) > 0.75:
					business['yelp'] = newurl
				else:
					# not found on yelp
					return
			else:
				# something weird is happening
				return
		else:
			# no luck
			return
	else:
		newurl = business['yelp']
		try:
			soup = BeautifulSoup(opener.open(newurl).read())
		except:
			return 
	header = soup.find('h1', class_="biz-page-title")
	if header:
		business['foundName'] = header.getText().strip(' \n').rstrip(' \n')
	website = soup.find('div', class_="biz-website")
	if website:
		siteAddress = website.find('a').getText().strip(' \n').rstrip(' \n')
		business['website'] = urllib2.unquote(siteAddress).decode("utf-8")
	phone = soup.find('span', class_="biz-phone")
	if phone:
		business['phone'] = phone.getText().strip(' \n').rstrip(' \n')
	address = soup.find('address')
	if address:
		span = address.find(itemprop="streetAddress")
		business['address'] = span.getText().strip(' \n').rstrip(' \n')

def getLink(siteName, links):
	linkString = ''
	for l in links:
		match = re.search(siteName, str(l['href']))
		if match:
			linkString = l['href']
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
		actualName = spell.getText()
		if type(actualName) is not unicode:
			actualName = unicode(actualName, 'utf-8')
		b['foundName'] = actualName
	phone = soup.find(text=re.compile("^(?:\([2-9]\d{2}\)\ ?|[2-9]\d{2}(?:\-?|\ ?))[2-9]\d{2}[- ]?\d{4}$"))
	if phone:
		business['phone'] = phone
	a = soup.find_all('a')
	for s in sites:
		business[s] = getLink(s, a)


for b in businesses:
	print "Search: " + b['searchName']
	b['found'] = False
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
	if not (b['website'] and b['address'] and b['phone']) and (not not b['yellowpages']):
		searchYellowpages(b)
	print b['foundName']
	if findMatchScore(b['searchName'], b['foundName']) > 0.75:
		b['found'] = True
		if b['website']:
			print "website: " + b['website']
		if b['phone']:
			b['phone'] = b['phone'].replace('(', '').replace(')', '').replace(' ', '.').replace('-', '.')
			print "phone: " + b['phone']
		if b['address']:
			print "address: " + b['address']
		if b['facebook']:
			print "facebook: " + b['facebook']
		if b['twitter']:
			print "twitter: " + b['twitter']
	else:
		print "probably not what you're looking for"
	print '\n'

for b in businesses:
	output.write("Search: " + b['searchName'] + '\n')
	if not b['found']:
		output.write("Not found" + '\n')
	else:
		output.write(b['foundName'] + '\n')
		printAttributes = ['address', 'phone', 'website', 'facebook', 'twitter']
		for att in printAttributes:
			if b[att]:
				if att == 'facebook' or att == 'twitter':
					output.write("{\field{\*\fldinst HYPERLINK "+att+"}{\fldrslt "+b[att]+"}}")
				output.write(b[att] + '\n')
	output.write('\n')


output.close()



