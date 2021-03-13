class Warnings:

    @staticmethod
    def database_player(database, user_id):
        user_data = database.select().where(database.id == user_id).get()
        if user_data:
            return True

    @staticmethod
    def quiz_create(database, user_id):
        user_data = database.select().where(database.id == user_id).get().state
        if user_data in (1, 2, 3):
            return True

    @staticmethod
    def quiz_play(database, user_id):
        user_data = database.select().where(database.id == user_id).get().state
        if user_data in (4, 5):
            return True
