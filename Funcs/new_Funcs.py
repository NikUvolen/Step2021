# -*- coding: utf-8 -*-

from os.path import normpath
from uuid import uuid4
import json
from re import findall

import peewee

from Funcs.VkBot import VkBot, DotDict
from Funcs.settings.token import token, group_id
from Funcs.settings.SupportFunctions import init_user, change_user_state, change_user_quest_state
from Funcs.settings.warnings import Warnings


database = peewee.SqliteDatabase(normpath('database/user_db.db'))
vk_bot = VkBot(group_id=group_id, token=token)
labels = DotDict({
    'menu': ['Список викторин', 'Пройти викторину', 'Посмотреть свой счёт', 'Создать викторину']
})


"""----- DATABASE -----"""


class BaseClass(peewee.Model):
    class Meta:
        database = database


class UsersTable(BaseClass):
    id = peewee.PrimaryKeyField(null=False)
    first_name = peewee.CharField(max_length=30)
    last_name = peewee.CharField(max_length=30)
    state = peewee.IntegerField(null=False)
    on_question_state = peewee.IntegerField()
    exp = peewee.IntegerField()


class QuizTable(BaseClass):
    user = peewee.ForeignKeyField(UsersTable)
    name_quiz = peewee.CharField(max_length=100)
    id_quiz = peewee.IntegerField()


class QuestionsTable(BaseClass):
    id_quiz = peewee.ForeignKeyField(QuizTable)
    question = peewee.CharField(max_length=511)
    id_question = peewee.CharField(unique=True)


class AnswersTable(BaseClass):
    id_questions = peewee.ForeignKeyField(QuestionsTable)
    answer1 = peewee.CharField(max_length=255)
    answer2 = peewee.CharField(max_length=255)
    answer3 = peewee.CharField(max_length=255, null=True)
    answer4 = peewee.CharField(max_length=255, null=True)
    current_answer = peewee.CharField(max_length=255)


class UsersAnswers(BaseClass):
    user = peewee.ForeignKeyField(UsersTable)
    quiz = peewee.ForeignKeyField(QuizTable)
    question_id = peewee.ForeignKeyField(QuestionsTable)
    user_answer = peewee.CharField()


"""---------------------"""


@vk_bot.message_handler(commands=['начать', 'Начать', 'start', 'Start'])
def welcome_menu(message):
    user = vk_bot.vk.method('users.get', {'user_ids': message.user_id})
    first_name, last_name = user[0]['first_name'], user[0]['last_name']

    if init_user(users_table=UsersTable, user_id=message.user_id, first_name=first_name, last_name=last_name):
        vk_bot.send_message(f'Добро пожаловать в DB-bot, {first_name}', message.user_id)
        vk_bot.send_image(message.user_id, normpath('img/0LavqKKl_aA.jpg'))

    vk_bot.upload_keyboard(['Меню'])
    vk_bot.send_message('Нажмите на "меню", чтобы посмотреть все мои функции:', message.user_id, keyboard=True)


@vk_bot.message_handler(commands=['меню', 'Меню'])
def menu(message):
    vk_bot.upload_keyboard(labels.menu, button_transfer=2)
    vk_bot.send_message('Моё меню:', message.user_id, keyboard=True)


@vk_bot.message_handler(commands=['список викторин', 'Список викторин'])
def quiz_list(message):
    list_quiz = [f'{q.id}) {q.name_quiz}' for num, q in enumerate(QuizTable.select())]
    vk_bot.upload_keyboard(labels.menu, button_transfer=2)
    instruction = '~ID викторины~ ) ~Название викторины~\n' + '{txt:-^80}\n'.format(txt='')
    if len(list_quiz) == 0:
        list_quiz.append('Пока тестов нет')
    vk_bot.send_message(instruction + '\n'.join(list_quiz), message.user_id, keyboard=True)


@vk_bot.message_handler(commands=['выйти', 'Выйти'])
def exit_quiz(message):
    vk_bot.upload_keyboard(labels.menu, button_transfer=2)

    if not Warnings.quiz_play(UsersTable, message.user_id) and not Warnings.quiz_create(UsersTable, message.user_id):
        vk_bot.send_message('Вы не создаёте викторину для этого действия', message.user_id, keyboard=True)

    quiz_id = ''

    try:
        file = open(normpath('database/intermediate_files.json'), 'r')
        intermediate_files = json.load(file)
        file.close()

        quiz_id = intermediate_files[str(message.user_id)]["quiz_id"]
        del intermediate_files[str(message.user_id)]

        file = open(normpath('database/intermediate_files.json'), 'w')
        json.dump(intermediate_files, file, indent=4)
        file.close()
    except KeyError:
        pass

    if Warnings.quiz_create(UsersTable, message.user_id):
        msg = f'Спасибо за Вашу викторину. Теперь для прохождения она доступна по id {quiz_id}'
    elif Warnings.quiz_play(UsersTable, message.user_id):
        msg = f'Спасибо за прохождение викторины.'
    else:
        msg = '.'

    change_user_state(UsersTable, message.user_id, 0)
    vk_bot.send_message(msg, message.user_id, keyboard=True)


@vk_bot.message_handler(commands=['посмотреть свой счёт', 'Посмотреть свой счёт'])
def view_invoice(message):
    user_score = UsersTable.select().where(UsersTable.id == message.user_id).get().exp
    vk_bot.upload_keyboard(['Меню'], button_transfer=2)
    vk_bot.send_message(f'У вас {user_score} баллов', message.user_id, keyboard=True)


@vk_bot.message_handler(commands=['пройти викторину', 'Пройти викторину'])
def quiz(message):
    change_user_state(UsersTable, message.user_id, 5)
    change_user_quest_state(UsersTable, message.user_id, 0)

    vk_bot.send_message('Введите id викторины', user_id=message.user_id)


@vk_bot.message_handler(func=lambda message: UsersTable.get(UsersTable.id == message.user_id).state == 5)
def take_quiz(message):
    try:
        quiz = QuizTable.get(QuizTable.id == message.body)
    except Exception:
        change_user_state(UsersTable, message.user_id, 0)

        vk_bot.upload_keyboard(labels.menu, button_transfer=2)
        vk_bot.send_message('Такого теста нет', message.user_id, keyboard=True)
        return

    change_user_state(UsersTable, message.user_id, 6)

    file = open(normpath('database/intermediate_files.json'), 'r')
    intermediate_files = json.load(file)
    file.close()

    intermediate_files[str(message.user_id)] = quiz.id

    file = open(normpath('database/intermediate_files.json'), 'w')
    json.dump(intermediate_files, file)
    file.close()

    vk_bot.upload_keyboard(['Начать викторину'])
    vk_bot.send_message(f'Викторина "{quiz.name_quiz}" от пользователя {quiz.user.first_name} {quiz.user.last_name}',
                        message.user_id, keyboard=True)


@vk_bot.message_handler(commands=['создать викторину', 'Создать викторину'])
def create_quiz(message):
    change_user_state(UsersTable, message.user_id, 2)
    change_user_quest_state(UsersTable, message.user_id, 0)

    vk_bot.send_message('Введите название викторины (не более 100 символов)', user_id=message.user_id)


@vk_bot.message_handler(func=lambda message: UsersTable.get(UsersTable.id == message.user_id).state == 2)
def create_quiz_2(message):
    print(message.body)
    if len(message.body) > 100:
        vk_bot.send_message('Символов больше 100. Введите ещё раз', message.user_id)
    else:
        user = UsersTable.get(UsersTable.id == message.user_id)
        quiz_id = str(uuid4())

        print(message.body, message)

        quiz_id = QuizTable.create(user=user, name_quiz=message.body, id_quiz=quiz_id)

        file = open(normpath('database/intermediate_files.json'), 'r')
        intermediate_files = json.load(file)
        intermediate_files[f"{user.id}"] = {'quiz_id': quiz_id.id}
        file.close()

        file = open(normpath('database/intermediate_files.json'), 'w')
        json.dump(intermediate_files, file, indent=4)
        file.close()

        change_user_state(UsersTable, message.user_id, 3)
        vk_bot.send_message(f'Ок, теперь введите вопрос №{user.on_question_state + 1} '
                            '(Пример: "В каком году умер Пушкин?")',
                            message.user_id)


@vk_bot.message_handler(func=lambda message: UsersTable.get(UsersTable.id == message.user_id).state == 3)
def questions(message):
    if len(message.body) > 511:
        vk_bot.send_message('Ваш вопрос слишком длинный. Сократите его до 512 символов', message.user_id)
    else:
        user = UsersTable.get(UsersTable.id == message.user_id)

        file = open(normpath('database/intermediate_files.json'), 'r')
        intermediate_files = json.load(file)
        file.close()

        quiz = QuizTable.get(QuizTable.id == intermediate_files[str(user.id)]['quiz_id'])
        QuestionsTable.create(id_quiz=quiz,
                              question=message.body,
                              id_question=str(quiz.id) + f'_{user.on_question_state}')

        change_user_state(UsersTable, message.user_id, 4)

        vk_bot.send_message('Введите до 4-х ответов в формате "ответ1_ответ2_!ответ3_ответ4", поставив перед '
                            'правильным восклицательный знак', message.user_id)


@vk_bot.message_handler(func=lambda message: UsersTable.get(UsersTable.id == message.user_id).state == 4)
def answer(message):
    if len(findall("!", message.body)) != 1:
        vk_bot.send_message('В ваших вариантах ответа нет восклицательного знака, либо их больше одного. '
                            'Введите ещё раз корректно, пожалуйста.', message.user_id)
        return

    answers = message.body.split('_')
    answers = answers + [None for _ in range(4 - len(answers))]
    current_answer = ''
    if 5 < len(answers) < 1:
        vk_bot.send_message('Вы ввели всего лишь {} ответов, но надо от 2-х до 4-х. Введите ещё раз', message.user_id)
        return

    for num, answ in enumerate(answers):
        if (answ is not None) and answ[0] == '!':
            answers[num] = answers[num][1:]
            current_answer = answ[1:]

    user = UsersTable.get(UsersTable.id == message.user_id)

    file = open(normpath('database/intermediate_files.json'), 'r')
    intermediate_files = json.load(file)
    file.close()

    quiz = QuizTable.get(QuizTable.id == intermediate_files[f'{user.id}']['quiz_id'])
    result = QuestionsTable.select().where(QuestionsTable.id_question == f'{quiz.id}_{user.on_question_state}').get()

    change_user_quest_state(UsersTable, message.user_id, user.on_question_state + 1)

    AnswersTable.create(id_questions=result,
                        answer1=answers[0],
                        answer2=answers[1],
                        answer3=answers[2],
                        answer4=answers[3],
                        current_answer=current_answer)

    change_user_state(UsersTable, message.user_id, 3)
    change_user_quest_state(UsersTable, message.user_id, user.on_question_state + 1)

    vk_bot.upload_keyboard(['Выйти'])
    vk_bot.send_message(f'Ок, теперь введите вопрос №{user.on_question_state + 2}', message.user_id, keyboard=True)


@vk_bot.message_handler(func=lambda message: UsersTable.get(UsersTable.id == message.user_id).state == 6)
def st_quiz(message):
    file = open(normpath('database/intermediate_files.json'), 'r')
    intermediate_files = json.load(file)
    quiz_id = intermediate_files[str(message.user_id)]
    file.close()

    user_qState = UsersTable.get(UsersTable.id == message.user_id).on_question_state
    if message.body.lower() != 'начать викторину':
        UsersAnswers.create(user=message.user_id,
                            quiz=QuizTable.get(QuizTable.id == quiz_id),
                            question_id=user_qState - 1,
                            user_answer=message.body)
        current_answer = AnswersTable.get(AnswersTable.id_questions == QuestionsTable.get(QuestionsTable.id_question == f'{quiz_id}_{user_qState - 1}'))
        if message.body == current_answer.current_answer:
            user_score = UsersTable.get(UsersTable.id == message.user_id)
            user_score.exp += 10
            user_score.save()

    try:
        """Если вопросы ещё остались"""

        question = QuestionsTable.select().where(QuestionsTable.id_question == f'{quiz_id}_{user_qState}').get()
        answers = AnswersTable.select().where(AnswersTable.id_questions == question).get()
        answers_list = [answers.answer1, answers.answer2, answers.answer3, answers.answer4]
        answers_list = [elem for elem in answers_list if elem is not None]

        print(message.body, answers.current_answer)

        change_user_quest_state(UsersTable, message.user_id, user_qState + 1)

        vk_bot.upload_keyboard(answers_list, button_transfer=len(answers_list) - 1)
        print(user_qState)
        vk_bot.send_message(f'Вопрос номер {user_qState + 1}) {question.question}', message.user_id, keyboard=True)

    except Exception:
        """Если вопросы закончились"""

        file = open(normpath('database/intermediate_files.json'), 'r')
        intermediate_files = json.load(file)
        file.close()

        del intermediate_files[str(message.user_id)]

        file = open(normpath('database/intermediate_files.json'), 'w')
        json.dump(intermediate_files, file)
        file.close()

        change_user_state(UsersTable, message.user_id, 0)
        change_user_quest_state(UsersTable, message.user_id, 0)

        vk_bot.upload_keyboard(labels.menu, button_transfer=2)
        score = UsersTable.get(UsersTable.id == message.user_id).exp
        vk_bot.send_message(f'Конец викторины. Ваш общий счёт {score} очков.', message.user_id)
