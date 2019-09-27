import json
import random
import linecache
import subprocess

class WordGen:
    def __init__(self, words):
        self.words = words
        output = subprocess.check_output(['wc', '-l', self.words])
        self.size = int(output.split()[0])

    def word(self):
        lineno = random.randint(0, self.size)
        return linecache.getline(self.words, lineno).strip()

word = WordGen('/usr/share/dict/words')

data = dict()
nodes = list()
links = list()

for i in range(0, random.randint(2, 10)):
    nodes.append({"name":word.word(),
                  "group":i})

for i in range(0, len(nodes)*2):
    target = source = 0
    while target == source:
        target = random.randint(0,len(nodes)-1)
        source = random.randint(0,len(nodes)-1)
    links.append({"source":source,
                  "target":target,
                  "value":10})

data["nodes"] = nodes
data["links"] = links

print(json.dumps(data))
