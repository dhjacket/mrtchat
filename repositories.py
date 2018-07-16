import jwt
import sqlalchemy as sa
from sqlalchemy.sql import and_, or_, not_

import db
from models import User, Chat, Message


class UserRepository:

    @staticmethod
    async def by_login(engine, login):
        async with engine.acquire() as conn:
            result = await conn.execute(db.users.select().where(db.users.c.login == login))
            user_row = await result.fetchone()
            return User(user_row['user_id'], user_row['login'], user_row['password']) if user_row else None


    @staticmethod
    async def by_id(engine, user_id):
        async with engine.acquire() as conn:
            result = await conn.execute(db.users.select().where(db.users.c.user_id == user_id))
            user_row = await result.fetchone()
            return User(user_row['user_id'], user_row['login'], user_row['password']) if user_row else None


    @staticmethod
    async def create(engine, login, password):
        hash_pass = User.salt_password(password)

        async with engine.acquire() as conn:
            result = await conn.execute(db.users.insert().values(login=login, password=hash_pass))
            user_row = await result.fetchone()
            await ChatRepository.add_user_to_chat(engine, 1, user_row['user_id'])

            user = await UserRepository.by_id(engine, user_row['user_id'])

            return user

    @staticmethod
    async def get_user_from_request(request):
        auth_token = request.cookies.get('token')
        if not auth_token:
            return None

        data = jwt.decode(auth_token, key=request.app.jwt_secret, algorithms='HS256')
        user = await UserRepository.by_login(request.app.db, data.get('login'))

        return user


class ChatRepository:

    @staticmethod
    async def create(engine):
        async with engine.acquire() as conn:
            result = await conn.execute(db.chats.insert().values())
            r = await result.fetchone()

            return Chat(r['chat_id'])

    @staticmethod
    async def add_user_to_chat(engine, chat_id, user_id):
        async with engine.acquire() as conn:
            await conn.execute(db.chat_users.insert().values(chat_id=chat_id, user_id=user_id))

    @staticmethod
    async def get_private_chat_id(engine, user_ids):
        async with engine.acquire() as conn:

            cu1 = db.chat_users.alias()
            cu2 = db.chat_users.alias()

            result = await conn.execute(
                sa.select([cu1.c.chat_id]).select_from(
                    cu1.join(cu2, cu1.c.chat_id == cu2.c.chat_id)
                ).where(
                    and_(
                        cu1.c.user_id == user_ids[0],
                        cu2.c.user_id == user_ids[1],
                        cu1.c.chat_id != 1)
                )
            )

            chat_user_row = await result.fetchone()
            if chat_user_row:
                return chat_user_row['chat_id']

            new_chat = await ChatRepository.create(engine)

            for user_id in user_ids:
                await conn.execute(db.chat_users.insert().values(chat_id=new_chat.chat_id, user_id=user_id))

            return new_chat.chat_id

    @staticmethod
    async def get_users_in_chat(engine, chat_id):
        async with engine.acquire() as conn:
            result = await conn.execute(
                sa.select([db.chat_users.c.user_id]).where(db.chat_users.c.chat_id == chat_id)
            )

        return [chat_user_row['user_id'] async for chat_user_row in result]


    @staticmethod
    async def check_user_in_chat(engine, chat_id, user_id):
        users_in_chat = await ChatRepository.get_users_in_chat(engine, chat_id)
        return user_id in users_in_chat


class MessageRepository:

    @staticmethod
    async def create(engine, user_id, text, chat_id):
        async with engine.acquire() as conn:
            result = await conn.execute(db.messages.insert().values(user_id=user_id, text=text, chat_id=chat_id))
            msg_row = await result.fetchone()
            return Message(msg_row['message_id'], text, user_id, chat_id)

    @staticmethod
    async def load_all(engine, chat_id):
        messages = []

        async with engine.acquire() as conn:
            result = await conn.execute(db.messages.select().where(db.messages.c.chat_id == chat_id))
            async for row in result:
                messages.append(Message(row['message_id'], row['text'], row['user_id'], row['chat_id']))

        return messages
