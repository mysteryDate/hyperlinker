A web-scraping project for the automatic retrieval of business phone numbers, addresses, facebooks, twitters and websites. Actual script is hyperlinker.py, everything else is input, output or test files. 

hyperlinker.py takes an input *.txt file with business names, each on an individual line (see the input/ folder). Output is generated to an *.rtf file, with embedded links and (hopefully) addresses translated to English.

Dependencies:
	- BeautifulSoup: http://www.crummy.com/software/BeautifulSoup/
	- pyLevenshtein: https://code.google.com/p/pylevenshtein/
	- rtfunicode: https://pypi.python.org/pypi/rtfunicode
	