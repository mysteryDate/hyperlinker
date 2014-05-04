import urllib2
import re
from bs4 import BeautifulSoup

url = 'https://www.google.ca/search?q=le+bierologue+montreal'
opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]
soup = BeautifulSoup(opener.open(url).read())

phoneNumbers = soup.find_all(text=re.compile("^(?:\([2-9]\d{2}\)\ ?|[2-9]\d{2}(?:\-?|\ ?))[2-9]\d{2}[- ]?\d{4}$"))

print phoneNumbers