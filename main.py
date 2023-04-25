import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import sqlite3

conn = sqlite3.connect('main.db')
cursor = conn.cursor()

def wait_for_more_data(driver):
    def more_data_loaded(driver):
        names = driver.find_elements(By.CSS_SELECTOR, "tr.row-RdUXZpkv.listRow")
        return len(names) > initial_data_count

    return more_data_loaded

browser = webdriver.Chrome()
url = 'https://ru.tradingview.com/markets/stocks-russia/market-movers-all-stocks/'
browser.get(url)

oscillators_buttons = WebDriverWait(browser, 10).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.content-mf1FlhVw"))
)
for button in oscillators_buttons:
    if button.text == "Осцилляторы":
        button.click()
        break

names_before = browser.find_elements(By.CSS_SELECTOR, "tr.row-RdUXZpkv.listRow")
initial_data_count = len(names_before)

load_more_button = WebDriverWait(browser, 10).until(
    EC.visibility_of_element_located((By.CSS_SELECTOR, '.loadButton-SFwfC2e0'))
)
load_more_button.click()
while True:
    try:
        load_more_button = WebDriverWait(browser, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '.loadButton-SFwfC2e0'))
        )
        load_more_button.click()
    except StaleElementReferenceException:
        continue
    except TimeoutException:
        break

content = browser.page_source
soup = BeautifulSoup(content, 'html.parser')

names = soup.find_all("tr", class_="row-RdUXZpkv listRow")
nomer = 0
for item in names:
    title = item.find("sup", class_="apply-common-tooltip tickerDescription-GrtoTeat").text
    ticker = item.find("a", class_="apply-common-tooltip tickerNameBox-GrtoTeat tickerName-GrtoTeat").text
    rsi_elements = item.find_all("td", class_="cell-RLhfr_y4 right-RLhfr_y4")
    if len(rsi_elements) >= 8:
        rsi = rsi_elements[7].text
    else:
        print("There are less than 8 elements on the page.")

    print(f"Компания: {title}  Тикер: {ticker}  rsi(14): {rsi}")
    nomer += 1

    # Проверка существующих данных в таблице stocks_data
    cursor.execute("SELECT * FROM stocks_data WHERE Company = ?", (title,))
    result = cursor.fetchone()

    # Если результат пуст, добавление данных в таблицу stocks_data
    if result is None:
        cursor.execute("INSERT INTO stocks_data (Company, Ticker) VALUES (?, ?)", (title, ticker))



print(nomer)
# Закрытие соединения с базой данных
conn.commit()
conn.close()

browser.quit()