# import sqlite3
# import peewee
# from random import random
#
#
# db = sqlite3.connect('test2DB.db')
# sql = db.cursor()
#
# sql.execute("""CREATE TABLE IF NOT EXISTS users (
#     login TEXT,
#     password TEXT,
#     cash BIGINT
# )""")
# db.commit()
#
#
# def register():
#     user_login = input('Login: ')
#     user_password = input('Password: ')
#
#     sql.execute(f"""SELECT login FROM users WHERE login = '{user_login}'""")
#     if sql.fetchone() is None:
#         sql.execute("""INSERT INTO users VALUES (?, ?, ?)""", (user_login, user_password, 0))
#         db.commit()
#     else:
#         print('Запись уже имеется')
#
#         for value in sql.execute("""SELECT * FROM users"""):
#             print(value)
#
#
# def casino():
#     user_login = input('Log in: ')
#     number = random()
#
#     sql.execute(f"""SELECT login FROM users WHERE login = '{user_login}'""")
#     if sql.fetchone() is None:
#         print('Вас нет в базе. Зарегистрируйтесь ')
#         register()
#     else:
#         if number > .6:
#             sql.execute(f"""UPDATE users SET cash = {1000} WHERE login = '{user_login}'""")
#             db.commit()
#         else:
#             print('Увы, вы проиграли(')
#
#
# casino()
#

from test import *


def test() -> int:
    return 5


citizen = Citizen(26, "Vasya", 'parket')
print(citizen)
