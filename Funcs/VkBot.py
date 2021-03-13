from random import randint
import logging

from vk_api import VkApi, VkUpload, bot_longpoll
from vk_api.bot_longpoll import VkBotLongPoll
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from termcolor import cprint, colored


class DotDict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, dct):
        super().__init__()
        for key, value in dct.items():
            if hasattr(value, 'keys'):
                value = DotDict(value)
            self[key] = value


class SupportFunctions:
    @staticmethod
    def get_random_id():
        return randint(0, 2 ** 20)

    @staticmethod
    def isint(n):
        try:
            int(n)
            return True
        except ValueError:
            return False

    @staticmethod
    def build_handler_dict(handler, **filters):
        return DotDict({'function': handler, 'filters': filters})


class VkBot:
    """Вк бот на базе Python 3.7"""

    def __init__(self, group_id, token):
        # logging.basicConfig(level=logging.ERROR, handlers=[logging.FileHandler('logs.log', 'w', 'utf-8')])

        self.group_id = group_id
        self.token = token
        self.message_list = []

        self.vk = VkApi(token=token)
        self.img = VkUpload(self.vk)
        self.keyboard = VkKeyboard(one_time=True)
        self.long_poller = VkBotLongPoll(self.vk, self.group_id)
        self.api = self.vk.get_api()
        self.funcs = SupportFunctions()

        self._requisites = ''

    def add_msg_handler(self, handler_dict):
        self.message_list.append(handler_dict)

    def _delete_keyboard(self):
        """Очищает клавиатуру"""
        self.keyboard.lines.clear()
        self.keyboard.lines.append([])

    def _upload_image(self, image_path):
        """Готовит картинку для отправки"""
        response = DotDict(self.img.photo_messages(image_path)[0])

        owner_id = response.owner_id
        photo_id = response.id
        access_key = response.access_key

        return owner_id, photo_id, access_key

    def upload_keyboard(self, labels: list, color=VkKeyboardColor.POSITIVE, button_transfer=None):
        """Загружает клавиатуру для отправки"""
        if len(labels) > 4:
            return
        for num, label in enumerate(labels):
            if button_transfer:
                if num == button_transfer:
                    self.keyboard.add_line()
            self.keyboard.add_button(label=label, color=color)

    def send_image(self, user_id, image_path, keyboard=False):
        """Отправляет картинку пользователю"""

        owner_id, photo_id, access_key = self._upload_image(image_path)
        attachment = f'photo{owner_id}_{photo_id}_{access_key}'

        self.api.messages.send(
            random_id=self.funcs.get_random_id(),
            peer_id=user_id,
            attachment=attachment,
            keyboard=self.keyboard.get_keyboard() if keyboard else None
        )
        self._delete_keyboard()

    def send_message(self, message, user_id, keyboard=False):
        """Отправляет сообщение пользователю"""
        self.api.messages.send(
            message=message,
            random_id=self.funcs.get_random_id(),
            peer_id=user_id,
            keyboard=self.keyboard.get_keyboard() if keyboard else None
        )
        if keyboard:
            self._delete_keyboard()

    def message_handler(self, commands=None, func=None, **kwargs):
        """ 'Пакует' функции в словрь, чтобы их вызывать дальше"""
        def wrapper(handler):
            handler_dict = self.funcs.build_handler_dict(handler,
                                                         commands=commands,
                                                         func=func,
                                                         **kwargs)
            self.add_msg_handler(handler_dict)
        return wrapper

    def run(self, event):
        event = DotDict(event)

        if event.type != 'message_new':
            print('не умею обрабатывать это: %s', event.type)

        def commands_check(commands, text):
            if commands is not None and text in commands:
                return True

        def funcs_check(func, requisites):
            if func is not None and func(requisites):
                return True

        requisites = event.object
        for msg in self.message_list:
            if commands_check(msg.filters.commands, requisites.body) and funcs_check(msg.filters.func, requisites):
                var = msg.function
                var(requisites)
                break
            if commands_check(msg.filters.commands, requisites.body) and msg.filters.func is None:
                var = msg.function
                var(requisites)
                break
            if funcs_check(msg.filters.func, requisites) and msg.filters.commands is None:
                var = msg.function
                var(requisites)
                break

    def _listen_longpoll(self):
        """ !!! Функция только для тестирования """
        cprint('START: \n\t>>> longpoll начал слушать сервер\nDEV:', color='yellow')

        def on_event(event):
            if event.type != bot_longpoll.VkBotEventType.MESSAGE_NEW:
                print('не умею обрабатывать это: %s', event.type)
            else:
                cprint(f'\t>>> {colored(event.obj.from_id, "red")}', color='yellow', end='')
                cprint(f' написал {colored(event.obj.text, "red")}', color='yellow')

            requisites = event.object
            requisites['user_id'] = requisites.pop('from_id')
            requisites['body'] = requisites.pop('text')

            def commands_check(commands: list, text: str) -> bool:
                if (commands is not None) and (text in commands):
                    return True

            def funcs_check(func, requisites):
                if (func is not None) and func(requisites):
                    return True

            for msg in self.message_list:

                if commands_check(commands=msg.filters.commands, text=requisites['body']):
                    if funcs_check(func=msg.filters.func, requisites=requisites):
                        msg.function(DotDict(requisites))
                        break

                if commands_check(commands=msg.filters.commands, text=requisites['body']):
                    if msg.filters.func is None:
                        msg.function(DotDict(requisites))
                        break

                if msg.filters.commands is None:
                    if funcs_check(func=msg.filters.func, requisites=requisites):
                        msg.function(DotDict(requisites))
                        break

        for event in self.long_poller.listen():
            try:
                on_event(event)
            except Exception as exc:
                cprint(f'ERROR: \n\t>>> {exc}', color='red')
                logging.exception(f'{exc}\nUSER_ID: {event.obj.peer_id}')
