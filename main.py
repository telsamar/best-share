import requests
from bs4 import BeautifulSoup

url = 'https://ru.tradingview.com/markets/stocks-russia/market-movers-overbought/'

# Отправка HTTP-запроса и получение содержимого страницы
response = requests.get(url)
content = response.content.decode('utf-8')

# Использование BeautifulSoup для парсинга HTML
soup = BeautifulSoup(content, 'html.parser')

names = soup.find_all("tr", class_="row-RdUXZpkv listRow")

for item in names:
    # title = item.get("data-rowkey")
    title = item.find("sup", class_="apply-common-tooltip tickerDescription-GrtoTeat").text
    ticker = item.find("a", class_="apply-common-tooltip tickerNameBox-GrtoTeat tickerName-GrtoTeat").text
    rsi = item.find("td", class_="cell-RLhfr_y4 right-RLhfr_y4").text

    print(f"title: {title} --- ticker: {ticker} --- rsi(14) 1d: {rsi}")
