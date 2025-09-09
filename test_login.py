import requests
url='http://127.0.0.1:8060/api.cgi'
resp = requests.post(url, data={'action':'login','username':'lorinta','password':'Password123!'})
print('STATUS', resp.status_code)
print(resp.text)
