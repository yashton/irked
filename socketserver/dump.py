import random
for i in range(2048):
    data = ""
    for i in range(0,250):
        data += chr(random.randrange(32, 126))
    print(data)
