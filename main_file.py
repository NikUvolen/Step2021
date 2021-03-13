import json
from flask import Flask, request
from Funcs.new_Funcs import *


app = Flask(__name__)


@app.route('/', methods=['POST'])
def runs():
    data = json.loads(request.data)
    if not data or 'type' not in data:
        return 'not ok'
    try:
        if data['type'] == 'message_new':
            vk_bot.run(event=data)
            print('ok')
        return 'ok'
    except Exception:
        return 'ok'


if __name__ == '__main__':
    # Базы данных лежат в Funcs.settings.databases
    database.connect()
    database.create_tables([UsersTable, QuizTable, QuestionsTable, AnswersTable])
    # vk_bot._listen_longpoll()
    app.run()
