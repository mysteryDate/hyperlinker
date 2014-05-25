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
class Render(QWebPage):
  def __init__(self, url):
    self.app = QApplication(sys.argv)
    QWebPage.__init__(self)
    self.loadFinished.connect(self._loadFinished)
    self.mainFrame().load(QUrl(url))
    self.app.exec_()

  def _loadFinished(self, result):
    self.frame = self.mainFrame()
    self.app.quit()

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]
# print("Which File: ")
# inFilePath = str(raw_input())
inFilePath = "input_may23.txt"
outFilePath = inFilePath.rpartition('.')[0] + "_HYPERLINKED.txt"

textFile = open(inFilePath, "U")
output = codecs.open(outFilePath, "w", 'utf-8')
fileData = textFile.readlines()
textFile.close()
businesses = []
sites = ['facebook', 'yelp', 'yellowpages', 'urbanspoon', 'twitter']

for line in fileData:
	name = unicode(line.rstrip(' \n').strip(), 'utf-8').replace('&', 'and')
	if name:
		if name[-1] == ':':
			continue
		else:
			businesses.append({'searchName': name})

for b in businesses:
	print b['searchName']

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

def searchFacebook(business):
	# pdb.set_trace()
	url = business['facebook']
	r = Render(url) # because javascript
	html = unicode(r.frame.toHtml())
	soup = BeautifulSoup(html)
	r.app.quit()
	if not business['address']:
		address = soup.find('span', itemprop='address')
		if address:
			business['address'] = address.find('a').getText()
	if not business['phone']:
		phone = soup.find('span', itemprop='telephone')
		if phone:
			business['phone'] = phone.getText()
	if not business['website']:
		website = soup.find('span', itemprop='url')
		if website:
			business['website'] = website.find('a').getText()

def searchYellowpages(business):
	# pdb.set_trace()
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
		siteAddress = urllib2.unquote(website.find('a')['href']).partition('=')[2].partition('&')[0]
		business['website'] = siteAddress
	phone = soup.find('span', class_="biz-phone")
	if phone:
		business['phone'] = phone.getText().strip(' \n').rstrip(' \n')
	address = soup.find('address')
	if address:
		span = address.find(itemprop="streetAddress")
		if span:
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

#only if twitter isn't found
def searchTwitter(business):
	name = unicodedata.normalize('NFKD', business['foundName']).encode('ascii','ignore')
	url = "https://twitter.com/search?q="+name.replace(' ', '%20')+"%20montreal&mode=users"
	soup = BeautifulSoup(opener.open(url).read())
	a = soup.find('a', 'js-user-profile-link')
	if a:
		link = a['href']
		if link:
			business['twitter'] = "twitter.com" + link

def searchGoogle(business):
	name = unicodedata.normalize('NFKD', business['searchName']).encode('ascii','ignore')
	url = "https://www.google.ca/search?q=" + name.replace(' ', '+').lower() + "+montreal"
	b['gsoup'] = BeautifulSoup(opener.open(url).read())
	soup = b['gsoup']
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
	# if not (b['website'] and b['address'] and b['phone']) and (not not b['facebook']):
		# searchFacebook(b)
	if not b['twitter']:
		searchTwitter(b)
	# pdb.set_trace()
	if not b['website']:
		ignorewords = ['restomontreal', 'googleusercontent', 'webcache', 'google', 'facebook', 'yelp', 'yellowpages', 'urbanspoon', 'twitter', 'foursquare', 'zagat', 'blogspot', 'tripadvisor']
		div = b['gsoup'].find('div', id='search')
		if div:
			a = div.find_all('a')
			for l in a:
				# pdb.set_trace()
				link = l['href']
				if link:
					ignore = False
					words = link.partition('//')[2].partition('/')[0].split('.')
					if not words[0]:
						continue
					for w in words:
						if w in ignorewords:
							ignore = True
					if not ignore:
						# pdb.set_trace()
						b['website'] = link.partition('&')[0].partition('=')[2]
						break

	print b['foundName']
	# if findMatchScore(b['searchName'], b['foundName']) > 0.75:
	if True:
		print findMatchScore(b['searchName'], b['foundName'])
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
	## write to file
	output.write("Search: " + b['searchName'] + '\n')
	if not b['found']:
		output.write("Not found" + '\n')
	else:
		output.write(b['foundName'] + '\n')
		printAttributes = ['address', 'phone', 'website', 'facebook', 'twitter']
		for att in printAttributes:
			if b[att]:
				output.write(b[att] + '\n')
	output.write('\n')


output.close()



