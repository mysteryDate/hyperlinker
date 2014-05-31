
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

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]
inFilePath = "inputs/may_17_input.txt"
outFilePath = "outputs/" + inFilePath.lstrip('inputs').rpartition('.')[0] + "_HYPERLINKED.rtf"
CITY = "montreal"

output = open(outFilePath, "w")
textFile = open(inFilePath, "U")
fileData = textFile.readlines()
textFile.close()
businesses = []
sites = ['facebook', 'yelp', 'yellowpages', 'urbanspoon', 'twitter']

# For translating addresses
roadTrans = {}
roadTrans['abbr'] = {'boul': 'boulevard', 'blvd': 'boulevard', 'bd': 'boulevard', 'ch': 'chemin', 
					'av': 'avenue', 'o': 'ouest', 'e': 'est', 'n': 'nord', 's': 'sud'}
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
		return ''
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
	bigR2 = 0 # if the input has MORE words than the solution (rare)
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
				business['address'] = translateAddress(span.getText().strip(' \n').rstrip(' \n'))
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
		url = "https://www.yelp.com/search?find_desc=" + name.replace(' ', '+').lower() + "&find_loc=" + CITY
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
				business['address'] = translateAddress(span.getText().strip(' \n').rstrip(' \n'))
			else:
				business['address'] = translateAddress(address.getText().strip(' \n').rstrip(' \n'))

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
	url = "https://twitter.com/search?q="+name.replace(' ', '%20')+"%20"+CITY+"&mode=users"
	soup = BeautifulSoup(opener.open(url).read())
	a = soup.find('a', 'js-user-profile-link')
	if a:
		link = a['href']
		if link:
			business['twitter'] = "twitter.com" + link

def searchGoogle(business):
	name = unicodedata.normalize('NFKD', business['searchName']).encode('ascii','ignore')
	url = "https://www.google.ca/search?q=" + name.replace(' ', '+').lower() + "+" + CITY
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
	pic = soup.find('img', src="/mapfiles/marker-noalpha.png")
	if pic:
		td = pic.parent.next_sibling
		if td:
			text = td.getText()	
			if text: #these nested condtionals are getting annoying
				reg = re.compile("[(]{0,1}\d{3}[) \.]{0,2}\d{3}[ -\.]{0,1}\d{4}")
				phone = reg.findall(text)
				if phone:
					b['phone'] = phone[0]
				b['address'] = translateAddress(text.partition('(')[0])
	return soup


output.write("{\\rtf1\\ansi\\ansicpg1252\\deff0\\deflang1033{" + 
	"\\fonttbl{\\f0\\fnil\\fcharset0 Helvetica;}}\\n{\\colortbl ;" + 
	"\\red0\\green0\\blue255;}\n{\\*\\generator Msftedit 5.41.21.2509;}" + 
	"\\viewkind4\\uc1\\pard\\sa200\\sl276\\slmult1\\lang9\\f0\\fs22\n\n")
for b in businesses:
	print "Search: " + b['searchName']
	b['foundName'] = b['searchName']
	b['address'] = ''
	b['phone'] = ''
	b['website'] = ''
	for s in sites:
		b[s] = ''
	# google is definitely on to me, I should be careful
	gsoup = searchGoogle(b)
	if b['foundName'] != b['searchName']:
		print "It's probably called: " + b['foundName']
	searchYelp(b)
	if not (b['website'] and b['address'] and b['phone']) and (not not b['yellowpages']):
		searchYellowpages(b)
	if not b['twitter']:
		searchTwitter(b)
	if not b['website']:
		# Sites I don't want showing up as the business website
		ignorewords = ['restomontreal', 'googleusercontent', 
		'webcache', 'google', 'facebook', 'yelp', 'yellowpages', 
		'urbanspoon', 'twitter', 'foursquare', 'zagat', 'blogspot', 
		'tripadvisor', 'pagesjaunes', 'montrealplus', 'canpages',
		'blackbookmag', 'adbeux', 'about', 'citeeze', 'nightlife',
		'restaurant', 'canplaces', 'yahoo', 'profilecanada', 'mtlblog'
		'nearyou', 'foodpages']
		div = gsoup.find('div', id='search')
		if div:
			h3 = div.find_all('h3', class_='r')
			a = []
			for header in h3:
				link = header.find('a')
				if link:
					a.append(link)
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
						ws = link.partition('&')[0].partition('=')[2]
						if ws[:4] == "http":
							ws = ws.lstrip("https://")
						ws = ws.rstrip('/')
						words = ws.split('/')
						if len(words) == 1: #ignore ones that are super lengthy and often wrong
							b['website'] = ws
							break
	print b['foundName']
	matchScore = findMatchScore(b['searchName'], b['foundName'])
	print matchScore
	if b['website']:
		if b['website'][:4] == "http":
			b['website'] = b['website'].lstrip("https://")
		if b['website'][:3] == "www":
			b['website'] = b['website'].partition("www.")[2]
		b['website'] = b['website'].rstrip('/')
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
	print '\n'
	## write to file
	if matchScore < 0.8:
		output.write("Search: " + b['searchName'].encode('rtfunicode') + '\line\n')
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