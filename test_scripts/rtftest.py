#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import pdb
import rtfunicode

output = open("test.rtf", "w")
name = unicode("Lumière", 'utf-8')
pdb.set_trace()

# This is just the rtf header, the whole point of using rtf
# is so that I can embed links
output.write("{\\rtf1\\ansi\\ansicpg1252\\deff0\\deflang1033{" + 
	"\\fonttbl{\\f0\\fnil\\fcharset0 Calibri;}}\\n{\\colortbl ;" + 
	"\\red0\\green0\\blue255;}\n{\\*\\generator Msftedit 5.41.21.2509;}" + 
	"\\viewkind4\\uc1\\pard\\sa200\\sl276\\slmult1\\lang9\\f0\\fs22\n\n")

output.write(name.encode('rtfunicode'))

output.write("}")
output.close()