python3 rand_tree.py > tree.json;
while [ 1 ]; do
    python3 rand_json.py "Received" "#0067FF" "Sent" "#FFA100" > data.json;
    python3 rand_json.py "Users" "#8100A6" > users.json;
    python3 rand_json.py "Messages" "#85FF00" > messages.json;
    sleep 4;
done
