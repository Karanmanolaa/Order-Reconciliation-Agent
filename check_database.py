import sqlite3


connection = sqlite3.connect("orders.db")

cursor = connection.cursor()

cursor.execute("SELECT * FROM orders")

orders = cursor.fetchall()

for order in orders:
    print(order)

connection.close()