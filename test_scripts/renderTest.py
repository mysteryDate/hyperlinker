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

		# Settings
		s = self.settings()
		s.setAttribute(QWebSettings.AutoLoadImages, False)
		s.setAttribute(QWebSettings.JavascriptCanOpenWindows, False)
		s.setAttribute(QWebSettings.PluginsEnabled, True)
		
		self.loadFinished.connect(self._loadFinished)
		self.mainFrame().load(QUrl(url))
		self.app.exec_()

	def _loadFinished(self, result):
		self.frame = self.mainFrame()
		self.app.quit()

	def load(self, url):
		QWebPage.__init__(self)
		self.loadFinished.connect(self._loadFinished)
		self.mainFrame().load(QUrl(url))
		self.app.exec_()



# r = Render(app, "http://stackoverflow.com/questions/6396541/web-scraping-multiple-links-with-pyqt-qtwebkit")
r = Render("https://www.song-swap.com")
html = unicode(r.frame.toHtml())
soup = BeautifulSoup(html)
pdb.set_trace()
r.load("http://boulevardtranslation.com/")
html = unicode(r.frame.toHtml())
soup = BeautifulSoup(html)
r.load("https://www.facebook.com/charles.francis")
html = unicode(r.frame.toHtml())
soup = BeautifulSoup(html)
r.app.quit()