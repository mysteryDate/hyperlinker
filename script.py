from pygoogle import pygoogle
import subprocess

g = pygoogle('lalime montreal')
g.pages = 2
g.__search__(True)