import urllib2
import re
from bs4 import BeautifulSoup

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

	a = soup.find_all('a')
	for link in a:
		match = re.search("facebook", str(link['href']))
		if match:
			fb = str(link['href'])
			break

	fb = fb.lstrip("/url?q=")
	b = fb.partition('&')[0]
	# print b

print businesses
