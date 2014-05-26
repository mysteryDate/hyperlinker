#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
roadTrans = {}

roadTrans['abbr'] = {'boul': 'boulevard', 'ch': 'chemin', 'av': 'avenue', 'o': 'ouest', 'e': 'est', 'n': 'nord', 's': 'sud'}
# key = french, value = english
roadTrans['type'] = {'rue': 'street', 'avenue': 'avenue', 'boulevard': 'boulevard', 'chemin': 'road'}
roadTrans['direction'] = {'ouest': 'west', 'nord': 'north', 'sud': 'south', 'est': 'east'}

print "Address: "
address = unicode(raw_input(), 'utf-8')
address = address.replace('.', '').replace(',', '').replace('-', ' ').lower()
print address

words = re.split(' ', address)
# replace abbreviations
for word in words:
	if word in roadTrans['abbr']:
		words.remove(word)
		words.append(roadTrans['abbr'][word])

print words

# remove and get good type
roadType = ''
direction = ''
for word in words:
	if word in roadTrans['type']:
		words.remove(word)
		roadType = roadTrans['type'][word]
	if word in roadTrans['direction']:
		words.remove(word)
		direction = roadTrans['direction'][word]

if roadType:
	words.append(roadType)
	words.append(direction)

#put it all together
final = []
for word in words:
	final.append(word.capitalize())

print ' '.join(final)

