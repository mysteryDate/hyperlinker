import urllib2
import re
from bs4 import BeautifulSoup

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]
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


for b in businesses:
	url = "https://www.google.ca/search?q=" + b['name'].replace(' ', '+').lower() + "+montreal"
	soup = BeautifulSoup(opener.open(url).read())
	b['phone numbers'] = soup.find_all(text=re.compile("^(?:\([2-9]\d{2}\)\ ?|[2-9]\d{2}(?:\-?|\ ?))[2-9]\d{2}[- ]?\d{4}$"))
	links = soup.find_all('cite')
	a = soup.find_all('a')
	fbstr = ''
	for link in a:
		match = re.search("facebook", str(link['href']))
		if match:
			fbstr = str((link['href']))
			break
	b['facebook'] = fbstr
	# b['facebook'] = fbstr.partition('&')[0]
	# b['facebook'] = b['facebook'].partition('=')[2]
	print "Name: " + str(b['name'])
	print "Phone: " + unicode(b['phone numbers'])
	print "Facebook: " + b['facebook']


