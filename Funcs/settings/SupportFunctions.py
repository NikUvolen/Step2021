import json
from os.path import normpath


def init_user(users_table, user_id: int, first_name: str, last_name: str) -> bool:
    try:
        users_table.create(id=user_id,
                           first_name=first_name,
                           last_name=last_name,
                           state=0,
                           on_question_state=0,
                           exp=0)
        return True
    except Exception:
        return False


def change_user_state(user_table, user_id, new_state):
    user_data = user_table.select().where(user_table.id == user_id).get()
    user_data.state = new_state
    user_data.save()


def change_user_quest_state(user_table, user_id, new_state):
    user_data = user_table.select().where(user_table.id == user_id).get()
    user_data.on_question_state = new_state
    user_data.save()
