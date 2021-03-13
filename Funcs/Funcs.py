# -*- coding: utf-8 -*-

from os.path import normpath, isfile
import json

import peewee

from VkBot import VkBot, DotDict
from settings.token import token, group_id
from settings.SupportFunctions import init_user, change_user_state, change_user_quest_state
from settings.warnings import Warnings


database = peewee.SqliteDatabase(normpath('database\\QuizDB'))
vk_bot = VkBot(group_id=group_id, token=token)

labels = DotDict({
    'menu': ['Пройти викторину', 'Посмотреть свой счёт', 'Создать викторину']
})


class BaseClass(peewee.Model):
    class Meta:
        database = database


class UsersTable(BaseClass):
    id = peewee.PrimaryKeyField(null=False)
    name = peewee.CharField(max_length=30)
    state = peewee.IntegerField(null=False)
    on_question_state = peewee.IntegerField()
    exp = peewee.IntegerField()


class QuestionsTable(BaseClass):
    id = peewee.ForeignKeyField(UsersTable)
    question = peewee.CharField(max_length=255)
    id_question = peewee.IntegerField(unique=True)


class AnswersTable(BaseClass):
    id_questions = peewee.ForeignKeyField(QuestionsTable)
    answer1 = peewee.CharField(max_length=255)
    answer2 = peewee.CharField(max_length=255)
    answer3 = peewee.CharField(max_length=255)
    answer4 = peewee.CharField(max_length=255)
    current_answer = peewee.CharField(max_length=255)


@vk_bot.message_handler(commands=['начать', 'Начать', 'start', 'Start'])
def welcome_menu(message):
    user_name = 'fdsf'

    init_user(users_table=UsersTable, user_id=message.user_id, user_name=user_name)

    vk_bot.upload_keyboard(['Меню'])
    vk_bot.send_message('Ваше меню:', message.user_id, keyboard=True)


@vk_bot.message_handler(commands=['выйти', 'Выйти'])
def exit_quiz(message):
    vk_bot.upload_keyboard(labels.menu, button_transfer=2)

    if not Warnings.quiz_play(UsersTable, message.user_id) and not Warnings.quiz_create(UsersTable, message.user_id):
        vk_bot.send_message('Вы не создаёте викторину для этого действия', message.user_id, keyboard=True)

    if Warnings.quiz_create(UsersTable, message.user_id):
        msg = f'Спасибо за Вашу викторину. Теперь для прохождения она доступна по вашему id {message.user_id}'
    elif Warnings.quiz_play(UsersTable, message.user_id):
        msg = f'Спасибо за прохождение викторины.'
    else:
        msg = '.'

    change_user_state(UsersTable, message.user_id, 0)
    vk_bot.send_message(msg, message.user_id, keyboard=True)


@vk_bot.message_handler(commands=['меню', 'Меню'])
def menu(message):
    welcome_msg = f"Добро пожаловать, в dm-bot."
    vk_bot.upload_keyboard(labels.menu, button_transfer=2)
    vk_bot.send_message(welcome_msg, message.user_id, keyboard=True)


@vk_bot.message_handler(commands=['посмотреть свой счёт', 'Посмотреть свой счёт'])
def view_invoice(message):
    user_score = UsersTable.select().where(UsersTable.id == message.user_id).get().exp
    vk_bot.upload_keyboard(['Меню'], button_transfer=2)
    vk_bot.send_message(f'У вас {user_score} баллов', message.user_id, keyboard=True)


@vk_bot.message_handler(commands=['пройти викторину', 'Пройти викторину'])
def quiz(message):
    change_user_state(UsersTable, message.user_id, 4)

    vk_bot.send_message('Введите id викторины', user_id=message.user_id)


@vk_bot.message_handler(func=lambda message: UsersTable.select().where(UsersTable.id == message.user_id).get().state == 1)
def start_quiz(message):
    change_user_state(UsersTable, message.user_id, 0)
    quiz_id = message.body


@vk_bot.message_handler(commands=['создать викторину', 'Создать викторину'])
def create_quiz(message):
    change_user_state(UsersTable, message.user_id, 2)

    vk_bot.send_message('Введите название викторины (не более 100 символов)', user_id=message.user_id)


@vk_bot.message_handler(func=lambda message: UsersTable.select().where(UsersTable.id == message.user_id).get().state == 2)
def create_quiz_2(message):
    if len(message.body) > 100:
        vk_bot.send_message('Символов больше 100. Введите ещё раз', message.user_id)
    else:
        # path = 'database\\questions'
        # files = [join(path, file) for file in listdir(path)]
        # files = [file for file in files if isfile(file)]
        # last_num_file = int(Path(max(files, key=getctime)).stem)
        with open(normpath(f'database\\questions\\{message.user_id}.json'), 'w', encoding='utf8') as file:
            temp = {'quiz_name': message.body, 'quiz': {}}
            json.dump(temp, file, indent=4)

        change_user_state(UsersTable, message.user_id, 3)
        vk_bot.send_message('Введите первый вопрос и ответ на него через вопрос и пробел '
                            '(Пример: "В каком году умер Пушкин? 1837")',
                            message.user_id)


@vk_bot.message_handler(func=lambda message: UsersTable.select().where(UsersTable.id == message.user_id).get().state == 3)
def questions(message):
    user_input = message.body.split('? ')
    if len(user_input) != 2:
        vk_bot.send_message('Что-то не так с Вашим вопросом. Введите ещё раз', message.user_id)
    else:
        question, answer = user_input
        with open(normpath(f'database\\questions\\{message.user_id}.json'), 'r', encoding='utf8') as file:
            user_dict = json.load(file)
            user_dict['quiz'][str(len(user_dict['quiz']))] = '_'.join([question, answer.lower()])
        with open(normpath(f'database\\questions\\{message.user_id}.json'), 'w', encoding='utf8') as file:
            json.dump(user_dict, file, ensure_ascii=False, indent=4)
        vk_bot.upload_keyboard(['Выйти'])
        vk_bot.send_message(f'Введи вопрос и ответ номер {len(user_dict["quiz"]) + 1} или нажми "выйти", '
                            f'чтобы завершить создание',
                            message.user_id, keyboard=True)


@vk_bot.message_handler(func=lambda message: UsersTable.select().where(UsersTable.id == message.user_id).get().state == 4)
def passing_quiz(message):
    change_user_quest_state(UsersTable, message.user_id, 0)
    change_user_state(UsersTable, message.user_id, 5)
    vk_bot.upload_keyboard(['Выйти'])
    if not isfile(normpath(f'database\\questions\\{message.body}.json')):
        vk_bot.send_message('Такой викторины не существует. Попробуйте ввести ещё раз или нажмите "выйти"',
                            message.user_id, keyboard=True)
    else:
        with open(normpath(f'database\\questions\\{message.user_id}.json'), 'r', encoding='utf8') as file:
            data = json.load(file)
            vk_bot.send_message(f"Викторина \'{data['quiz_name']}\'. Всего вопросов {len(data['quiz'])}. Поехали",
                                message.user_id)

            new_state = UsersTable.select().where(UsersTable.id == message.user_id).get().on_question_state + 1
            change_user_quest_state(UsersTable, message.user_id, new_state)
            question, answer = data["quiz"][str(new_state - 1)].split("_")
            vk_bot.send_message(f'Вопрос {new_state}) {question}?', message.user_id,
                                keyboard=True)


@vk_bot.message_handler(func=lambda message: UsersTable.select().where(UsersTable.id == message.user_id).get().state == 5)
def continue_quiz(message):
    new_state = UsersTable.select().where(UsersTable.id == message.user_id).get().on_question_state + 1
    change_user_quest_state(UsersTable, message.user_id, new_state)
    vk_bot.upload_keyboard(['Выйти'])
    with open(normpath(f'database\\questions\\{message.user_id}.json'), 'r', encoding='utf8') as file:
        data = json.load(file)
        try:
            question, answer = data["quiz"][str(new_state - 2)].split("_")
            if message.body.lower() == answer:
                user_data = UsersTable.select().where(UsersTable.id == message.user_id).get()
                user_data.exp += 5
                user_data.save()

                vk_bot.send_message('Правильно! + 5 баллов', message.user_id)
            question, answer = data["quiz"][str(new_state - 1)].split("_")
            vk_bot.send_message(f'Вопрос {new_state}) {question}?', message.user_id, keyboard=True)
        except KeyError:
            vk_bot.send_message('Конец викторины', message.user_id, keyboard=True)

