from bs4 import BeautifulSoup
import requests

url = 'https://xueqiu.com/S/SH600519'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3742.400 QQBrowser/10.5.3864.400'}

session = requests.session()
# session.get(url='https://xueqiu.com/', headers=headers, timeout=10)
# text = session.get(url, headers=headers, timeout=10).text
text = requests.get(url, headers=headers).text
soup = BeautifulSoup(text, 'lxml')
print(soup.prettify())  # 格式化代码，自动补全代码，进行容错的处理
