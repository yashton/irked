#! /usr/bin/python3

print("escape ^\\\\\\")

for i in range(1,33):
    print("screen -t demo%d %d irssi -c localhost -p 6667 -n ashton%d -h testing" % (i, i, i))

for i in range(1, 33):
    print("select %d\nfocus down" % i)

print("sessionname irked_demo")
print("startup_message off")
