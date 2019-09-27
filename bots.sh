#! /bin/bash

for i in {0..31}; do
    python3 bot.py $1 6666 "bot$i" "bot$i" "#demo"$((i / 2)) > /dev/null &
done;
