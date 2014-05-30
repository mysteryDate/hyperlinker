
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import re
from bs4 import BeautifulSoup
import Levenshtein
import unicodedata
import codecs
import rtfunicode
import pdb

#for pages with javascript
# from PyQt4.QtGui import *
# from PyQt4.QtCore import *
# from PyQt4.QtWebKit import *
# import sys
# class Render(QWebPage):
#   def __init__(self, url):
#     self.app = QApplication(sys.argv)
#     QWebPage.__init__(self)
#     self.loadFinished.connect(self._loadFinished)
#     self.mainFrame().load(QUrl(url))
#     self.app.exec_()

#   def _loadFinished(self, result):
#     self.frame = self.mainFrame()
#     self.app.quit()

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]
# print("Which File: ")
# inFilePath = str(raw_input())
inFilePath = "input.txt"
outFilePath = "outputs/" + inFilePath.rpartition('.')[0] + "_HYPERLINKED.rtf"

# output = codecs.open(outFilePath, "w", 'utf-8')
output = open(outFilePath, "w")
# pdb.set_trace()
textFile = open(inFilePath, "U")
fileData = textFile.readlines()
textFile.close()
businesses = []
sites = ['facebook', 'yelp', 'yellowpages', 'urbanspoon', 'twitter']
# pdb.set_trace()

# For translating addresses
roadTrans = {}
roadTrans['abbr'] = {'boul': 'boulevard', 'blvd': 'boulevard', 'ch': 'chemin', 'av': 'avenue', 'av': 'avenue', 'o': 'ouest', 'e': 'est', 'n': 'nord', 's': 'sud'}
# key = french, value = english
roadTrans['type'] = {'rue': 'street', 'avenue': 'avenue', 'boulevard': 'boulevard', 'chemin': 'road'}
roadTrans['direction'] = {'ouest': 'west', 'nord': 'north', 'sud': 'south', 'est': 'east'}

for line in fileData:
	name = unicode(line.rstrip(' \n').strip(), 'utf-8').replace('&', 'and')
	if name:
		if name[-1] == ':':
			continue
		else:
			businesses.append({'searchName': name})

def removeSkipWords(words):
	skipWords = ['au', 'le', 'de', 'the']
	for w in words:
		for s in skipWords:
			if w.lower() == s:
				words.remove(w)
	return words

def translateAddress(stringAddress):
	s = stringAddress
	address = {}
	numRegex = re.compile("\A\d{1,5}[A-Z]{1}[ ,]|\A\d{1,5}", re.UNICODE)
	# pdb.set_trace()
	num = numRegex.findall(s)
	# Get out number and street
	if num:
		num = num[0].rstrip(' ,')
		s = s.replace(num, '').lstrip(' ,')
		s = s.lstrip()
		address['number'] = num
		address['street'] = s.partition(',')[0].rstrip(' \n').lower()
	else:
		print "problem with ", s
		return s
	# Translate
	street = address['street'].split()
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
	address['street'] = ' '.join(street).rstrip()
	return address['number'] + ' ' + address['street']


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
	if not business['phone']:
		phone = soup.find('span', class_="biz-phone")
		if phone:
			business['phone'] = phone.getText().strip(' \n').rstrip(' \n')
	if not business['address']:
		addy = soup.find_all('address')
		if addy:
			address = addy[-1]
			span = address.find(itemprop="streetAddress")
			if span:
				business['address'] = span.getText().strip(' \n').rstrip(' \n')
			else:
				business['address'] = address.getText().strip(' \n').rstrip(' \n')

def getLink(siteName, links):
	linkString = ''
	for l in links:
		if 'class' in l.attrs: #ignore these, they're for googleplus, etc.
			continue
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
	pic = soup.find('img', src="/mapfiles/marker-noalpha.png")
	if pic:
		td = pic.parent.next_sibling
		if td:
			text = td.getText()	
			if text: #these nested condtionals are getting annoying
				if not b['phone']:
					b['phone'] = '(' + text.partition('(')[2]
				if not b['address']:
					b['address'] = text.partition('(')[0]


output.write("{\\rtf1\\ansi\\ansicpg1252\\deff0\\deflang1033{" + 
	"\\fonttbl{\\f0\\fnil\\fcharset0 Calibri;}}\\n{\\colortbl ;" + 
	"\\red0\\green0\\blue255;}\n{\\*\\generator Msftedit 5.41.21.2509;}" + 
	"\\viewkind4\\uc1\\pard\\sa200\\sl276\\slmult1\\lang9\\f0\\fs22\n\n")
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
	if not b['website']:
		ignorewords = ['restomontreal', 'googleusercontent', 
		'webcache', 'google', 'facebook', 'yelp', 'yellowpages', 
		'urbanspoon', 'twitter', 'foursquare', 'zagat', 'blogspot', 
		'tripadvisor', 'pagesjaunes', 'montrealplus', 'canpages',
		'blackbookmag', 'adbeux', 'about', 'citeeze', 'nightlife',
		'restaurant', 'canplaces', 'yahoo']
		div = b['gsoup'].find('div', id='search')
		if div:
			a = div.find_all('a')
			for l in a:
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
						b['website'] = link.partition('&')[0].partition('=')[2]
						break
	print b['foundName']
	print findMatchScore(b['searchName'], b['foundName'])
	b['found'] = True
	if b['website']:
		print "website: " + b['website']
	if b['phone']:
		b['phone'] = b['phone'].replace('(', '').replace(')', '').replace(' ', '.').replace('-', '.')
		print "phone: " + b['phone']
	if b['address']:
		b['address'] = translateAddress(b['address'])
		print "address: " + b['address']
	if b['facebook']:
		print "facebook: " + b['facebook']
	if b['twitter']:
		print "twitter: " + b['twitter']
	print '\n'
	## write to file
	output.write("Search: " + b['searchName'].encode('rtfunicode') + '\line\n')
	if not b['found']:
		output.write("Not found" + ' \line\n')
	else:
		output.write(b['foundName'].encode('rtfunicode') + ' \line\n')
		printAttributes = ['address', 'phone', 'website', 'facebook', 'twitter']
		for att in printAttributes:
			if b[att]:
				if att == 'website':
					name = urllib2.unquote(b[att])
					name = unicode(urllib2.unquote(name), 'utf-8')
					output.write("{\\field{\\*\\fldinst{HYPERLINK " + b[att].encode('rtfunicode') + "}}{\\fldrslt{\ul\cf1" + name.encode('rtfunicode') + "}}}" + ' \line\n');
					continue
				elif att == 'facebook' or att == 'twitter':
					output.write("{\\field{\\*\\fldinst{HYPERLINK " + b[att].encode('rtfunicode') + "}}{\\fldrslt{\ul\cf1" + att.capitalize() + "}}}" + ' \line\n');
					name = urllib2.unquote(b[att])
					name = unicode(urllib2.unquote(name), 'utf-8')
					output.write(name.encode('rtfunicode') + ' \line\n')
				else:
					output.write(b[att].encode('rtfunicode') + ' \line\n')
	output.write('\line\n\n')

output.write('}')
output.close()



