from bs4 import BeautifulSoup
import requests
import os

soup = BeautifulSoup(open('html', encoding='utf-8'), 'html.parser')
i = 1
for audio in soup.find_all('audio'):
    url = audio['src']
    if url == '':
        continue
    print(url)
    file = 'mp3/' + str(i) + '.mp3'
    i += 1
    if os.path.exists(file):
        continue
    res = requests.get(url, stream=True)
    with open(file, 'wb') as fd:
        fd.write(res.content)
        fd.flush()
