import sqlite3

conn = sqlite3.connect('main.db')
cursor = conn.cursor()

table_columns = ', '.join([f'"{i}" INTEGER' for i in range(1, 26)])
sql = f'''CREATE TABLE IF NOT EXISTS stocks_data (
    Company TEXT,
    Ticker TEXT,
    {table_columns}
);'''

cursor.execute(sql)

conn.commit()
conn.close()