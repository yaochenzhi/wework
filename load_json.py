import json


with open('wework.cfg') as f:
    jsonData = json.load(f)

print(jsonData)