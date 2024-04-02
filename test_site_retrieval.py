import requests

test_url = 'http://web.archive.org/web/20000229104652im_/http://a996.g.akamaitech.net/7/996/975/efaef77c365896/www.nike.com/home/images/featuring.gif'
response = requests.get(test_url)
print(response.status_code)
