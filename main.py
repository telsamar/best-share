import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date, timedelta
import schedule
import time
import os

# Сдвигает данные влево на одну позицию в таблице stocks_data
def shift_data_left(cursor, conn):
    for i in range(1, 25):
        cursor.execute(f'UPDATE stocks_data SET "{i}" = "{i + 1}"')
    cursor.execute('UPDATE stocks_data SET "25" = NULL')
    conn.commit()

# Устанавливает соединение с базой данных и возвращает объекты conn и cursor
def connect_to_database(database_name):
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()
    return conn, cursor

# Инициализирует веб-драйвер и открывает указанный URL
def setup_webdriver():
    browser = webdriver.Chrome()
    url = 'https://ru.tradingview.com/markets/stocks-russia/market-movers-all-stocks/'
    browser.get(url)
    return browser

 # Находит и нажимает кнопку "Осцилляторы" на веб-странице
def click_oscillators_button(browser):
    oscillators_buttons = WebDriverWait(browser, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.content-mf1FlhVw"))
    )
    for button in oscillators_buttons:
        if button.text == "Осцилляторы":
            button.click()
            break

# Загружает все данные на веб-странице, кликая на кнопку "Загрузить еще"
def load_all_data(browser):
    names_before = browser.find_elements(By.CSS_SELECTOR, "tr.row-RdUXZpkv.listRow")
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
    return soup

# Обрабатывает данные, извлеченные из soup rsi, и обновляет базу данных
def process_data(soup, cursor, conn):
    names = soup.find_all("tr", class_="row-RdUXZpkv listRow")
    nomer = 0

    for item in names:
        title, ticker, rsi = extract_data_from_item(item)

        # print(f"Компания: {title}  Тикер: {ticker}  rsi(14): {rsi}")
        nomer += 1
        
        try:
            update_database(cursor, conn, title, ticker, rsi)
        except sqlite3.Error as e:
            print(f"Ошибка обновления базы данных: {e}")

        plot_graph(ticker, conn)

    print(f"Всего обнаружено {nomer} акции")

# Извлекает название компании, тикер и RSI из элемента данных
def extract_data_from_item(item):
    title = item.find("sup", class_="apply-common-tooltip tickerDescription-GrtoTeat").text
    ticker = item.find("a", class_="apply-common-tooltip tickerNameBox-GrtoTeat tickerName-GrtoTeat").text
    rsi_elements = item.find_all("td", class_="cell-RLhfr_y4 right-RLhfr_y4")
    if len(rsi_elements) >= 8:
        rsi = rsi_elements[7].text
    else:
        print("There are less than 8 elements on the page.")
        rsi = None
    return title, ticker, rsi

# Обновляет базу данных, добавляя или обновляя записи с данными о компании
def update_database(cursor, conn, title, ticker, rsi):
    cursor.execute("SELECT * FROM stocks_data WHERE Company = ?", (title,))
    result = cursor.fetchone()

    if result is None:
        insert_data(cursor, title, ticker)

    if result is not None:
        update_rsi_value(cursor, conn, title, rsi)
    else:
        print("Запись с заданным title не найдена.")

# Вставляет новую запись в таблицу stocks_data с данными о компании
def insert_data(cursor, title, ticker):
    cursor.execute("INSERT INTO stocks_data (Company, Ticker) VALUES (?, ?)", (title, ticker))

# Обновляет значение RSI для существующей записи в таблице stocks_data
def update_rsi_value(cursor, conn, title, rsi):
    if rsi is not None:
        cursor.execute("UPDATE stocks_data SET '25' = ? WHERE Company = ?", (rsi, title))
        conn.commit()
    else:
        print("Значение RSI отсутствует.")

# Построение графика 
def plot_graph(ticker, conn):
    df = pd.read_sql_query(f"SELECT * FROM stocks_data WHERE Ticker = '{ticker}'", conn)
    if df.empty:
        print(f"Данные для {ticker} не найдены.")
        return
    columns = [str(i) for i in range(1, 26)]
    data = df.loc[:, columns].values[0]
    processed_data = []
    for x in data:
        if x in ["—", None]:
            processed_data.append(np.nan)
        else:
            processed_data.append(float(x))
    plt.plot(columns, processed_data, marker='o', markersize=4)  # Установка жирности точек
    plt.title(f"График RSI (14) 1д для {ticker}")
    plt.xlabel("Период")
    plt.ylabel("Значение RSI")
    plt.ylim([0, 100])
    today = date.today()
    dates = [today - timedelta(days=i) for i in range(0, 25)]
    plt.xticks(columns, [date.strftime("%Y-%m-%d") for date in dates[::-1]], rotation=90, ha='center')
    # Добавление подписей значений по оси Y рядом с точками
    for i, value in enumerate(processed_data):
        if not np.isnan(value):
            plt.text(i, value + 2, f"{value:.1f}", ha='left', va='bottom', fontsize=8, rotation=90)

    filename = f"{ticker}.png"    
    plt.savefig(f"graph/{filename}", bbox_inches='tight')
    plt.clf()

def clear_directory(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # Удаляем файлы и символические ссылки
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Удаляем папки
        except Exception as e:
            print(f"Ошибка при удалении {file_path}: {e}")

def connect_to_db_and_shift_data():
    try:
        conn, cursor = connect_to_database('main.db')
    except sqlite3.Error as e:
        print(f"Ошибка соединения с базой данных: {e}")
        exit()
    return conn, cursor


def main():
    print("Запуск задачи...")
    graph_directory = "graph"
    clear_directory(graph_directory)
    conn, cursor = connect_to_db_and_shift_data()
    shift_data_left(cursor, conn)
    
    try:
        browser = setup_webdriver()
    except Exception as e:
        print(f"Ошибка при инициализации веб-драйвера: {e}")
        exit()

    click_oscillators_button(browser)
    soup = load_all_data(browser)
    process_data(soup, cursor, conn)

    conn.commit()
    conn.close()
    browser.quit()
    print("Задача завершена.")

if __name__ == "__main__":
    print("Начата задача по расписанию.")
    # schedule.every().day.at("13:37").do(main)
    main()
    print("Ожидание выполнения задачи.")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Ждать 60 секунд перед повторной проверкой
    print("Задача выполнена.")