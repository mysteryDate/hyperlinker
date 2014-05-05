import urllib2
import re
from bs4 import BeautifulSoup

# print("Which File: ")
# inFilePath = str(raw_input())
inFilePath = "input.txt"
outFilePath = inFilePath.rstrip('.txt') + "_HYPERLINKED.txt"

textFile = open(inFilePath, "U")
output = open(outFilePath, "w")
fileData = textFile.readlines()
textFile.close()
businesses = []

for line in fileData:
	s = line.rstrip('\n')
	businesses.append({'name': s})

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]

for b in businesses:
	url = "https://www.google.ca/search?q=" + b['name'].replace(' ', '+').lower() + "+montreal"
	soup = BeautifulSoup(opener.open(url).read())
	b['phone numbers'] = soup.find_all(text=re.compile("^(?:\([2-9]\d{2}\)\ ?|[2-9]\d{2}(?:\-?|\ ?))[2-9]\d{2}[- ]?\d{4}$"))
	links = soup.find_all('cite')
	facebookLinks = []
	for l in links:
		match = re.search('facebook', str(l))
		if match:
			facebookLinks.append(str(l))
	for l in facebookLinks:
		l = l.replace("<b>", '')
		l = l.replace("</b>", '')
		l = l.replace("<cite>", '')
		l = l.replace("</cite>", '')
	b['facebook links'] = facebookLinks
	print "Name: " + str(b['name'])
	print "Phone: " + str(b['phone numbers'])
	print "Facebook: " + str(b['facebook links'])


