import asyncio
import logging

from aiohttp import web
from aiopg.sa import create_engine

import db
import handlers
from middlewares import check_auth, set_user
from settings import *


async def on_shutdown(app):
    app.broadcast_task.cancel()
    for ws in app.ws_connections.values():
        await ws[1].close(code=1001, message='Server shutdown')


async def init_pg(app):
    engine = await create_engine(
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT,
        loop=app.loop)

    app.db = engine
    async with engine.acquire() as conn:
        with open('init.sql') as f:
            sql = f.read()

        await conn.execute(sql)
        res = await conn.execute(db.chats.select().where(db.chats.c.chat_id == 1))
        if not await res.fetchone():
            await conn.execute(db.chats.insert().values())


async def close_pg(app):
    app.db.close()
    await app.db.wait_closed()


async def broadcast_loop(app):
        while True:
            msg, user_ids = await app.msg_queue.get()
            for user_id in user_ids:
                user_and_ws = app.ws_connections.get(user_id)
                if user_and_ws:
                    await user_and_ws[1].send_str(str(msg))


app = web.Application(middlewares=[set_user, check_auth])

app.on_startup.append(init_pg)

app.on_cleanup.append(on_shutdown)
app.on_cleanup.append(close_pg)

logger = logging.getLogger('app')
logger.setLevel(logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logger.addHandler(console)

app.logger = logger

ws_handler = handlers.WebSocketHandler()
history_handler = handlers.HistoryHandler()

app.router.add_route('POST', '/register/', handlers.register_handler, name='register')
app.router.add_route('POST', '/login/', handlers.login_handler, name='login')
app.router.add_route('GET', '/users/', handlers.active_users_handler, name='active_users')
app.router.add_route('GET', '/chat/', ws_handler.handle_chat_ws, name='chat')
app.router.add_route('GET', r'/history/chat/{chat_id:[0-9]*}/', history_handler.handle_chat_history, name='chat_history')
app.router.add_route('GET', r'/history/user/{user_id:[0-9]*}/', history_handler.handle_user_history, name='user_history')


app.ws_connections = {}  # {User.user_id: (User, WebSocketConnection)}
app.jwt_secret = JWT_SECRET

app.msg_queue = asyncio.Queue()

app.broadcast_task = asyncio.Task(broadcast_loop(app))

app.logger.info('App started: host=%s, port=%s' % (APP_HOST, APP_PORT))
web.run_app(app, host=APP_HOST, port=APP_PORT)


