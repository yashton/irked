import random
import json
import sys
import time

data = []
for i in range(1, len(sys.argv), 2):
    label, color = sys.argv[i:i+2]
    data_set = list()
    stamp = int(time.time()) - 200;
    value = 0
    for j in range(0, 60):
        stamp += random.randint(1, 5)
        delta = random.randint(-100, 100)
        if 1024 < (value + delta) or (value + delta) < 0:
            value -= delta
        else:
            value += delta
        data_set.append([stamp * 1000, value])
    data.append({'label': label, 'data': data_set, 'color': color})
print(json.dumps(data))
