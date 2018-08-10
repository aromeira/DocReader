import requests
import json

json_file = json.load(open('/home/danielle/projects/python/pyParseDocts/input.json'))

r = requests.post('http://localhost:10080', data={'json':json.dumps(json_file)})

print('RETCODE [' + r.status_code + ']')
print(r.json())