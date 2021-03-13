from os.path import normpath
from enum import Enum

db_file = normpath('../database/userstates')


class States(Enum):
    S_START = '0'
    S_CHOICE_LANGUAGE = '1'
    S_MENU = '2'
    S_WARNING_CHOICE_HERO = '3'
    S_CHOICE_HERO = '4'
    S_IN_GAME = '5'
    S_IN_SHOP = '6'
