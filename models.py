import hashlib

from settings import *


class User:

    def __init__(self, user_id, login, password):
        self.user_id = user_id
        self.login = login
        self._password = password

    @staticmethod
    def salt_password(password):
        salted = hashlib.md5()
        salted.update(password.encode('utf-8'))
        salted.update(PASSWORD_SALT.encode('utf-8'))

        return salted.hexdigest()

    def check_password(self, password):
        return self._password == User.salt_password(password)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'login': self.login
        }


class Message:

    def __init__(self, message_id, text, user_id, chat_id):
        self.message_id = message_id
        self.text = text
        self.user_id = user_id
        self.chat_id = chat_id

    def to_dict(self, context=None):
        result = {
            'message_id': self.message_id,
            'from': self.user_id,
            'text': self.text
        }

        if context:
            if context.get('mode') == 'group':
                result['chat_id'] = self.chat_id
            elif context.get('mode') == 'private':
                result['to'] = context.get('to')

        return result


class Chat:

    def __init__(self, chat_id):
        self.chat_id = chat_id
        # TODO chat_type?