import json

import aiohttp
from aiohttp import web

from repositories import *


async def register_handler(request):
    # TODO brute force check
    data = await request.json()  # TODO JSON validation

    if not data.get('login') or not data.get('password'):
        return web.json_response({'ok': False, 'error': 'login_or_password_missing'}, status=400)

    user = await UserRepository.by_login(request.app.db, data.get('login'))

    if user:
        return web.json_response({'ok': False, 'error': 'login_already_exists'}, status=400)

    await UserRepository.create(request.app.db, data.get('login'), data.get('password'))
    return web.json_response({'ok': True})


async def login_handler(request):
    # TODO brute force check
    data = await request.json()  # TODO JSON validation

    if not data.get('login') or not data.get('password'):
        return web.json_response({'ok': False, 'error': 'login_or_password_missing'}, status=400)

    user = await UserRepository.by_login(request.app.db, data.get('login'))

    if not user or not user.check_password(data['password']):
        return web.json_response({'ok': False}, status=401)

    token = jwt.encode({'login': user.login, 'id': user.user_id}, request.app.jwt_secret, algorithm='HS256')

    response = web.Response(body=token)
    response.cookies['token'] = str(token, 'utf-8')

    return response


async def active_users_handler(request):
    return web.json_response(
        [user_and_ws[0].to_dict() for user_and_ws in request.app.ws_connections.values()]
    )


class WebSocketHandler:

    def __init__(self):
        pass

    async def handle_chat_ws(self, request):

        ws = web.WebSocketResponse()
        await ws.prepare(request)

        request.user = await UserRepository.get_user_from_request(request)
        request.app.ws_connections[request.user.user_id] = (request.user, ws)

        request.app.logger.info('User %s connected' % request.user.user_id)

        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.close:
                request.app.logger.info('User %s disconnected' % request.user.user_id)
                break
            elif msg.type == aiohttp.WSMsgType.error:
                request.app.logger.info('User %s connection closed with error %s' % (request.user.id, ws.exception()))
                break
            elif msg.type == aiohttp.WSMsgType.text:
                message = msg.data
                await self.on_new_message(request, message)
            else:
                request.app.logger.info('ws connection received unknown message type %s' % msg.type)

        await ws.close()
        del request.app.ws_connections[request.user.user_id]
        request.app.logger.info('User %s disconnected' % request.user.user_id)

        return ws

    async def on_new_message(self, request, message):
            message = json.loads(message)
            chat_id = message.get('chat_id')
            if message.get('type') == 'new_group_msg':
                if not await ChatRepository.check_user_in_chat(request.app.db, chat_id, request.user.user_id):
                    request.app.logger.info('Message to wrong chat')
                    return

                msg = await MessageRepository.create(
                    request.app.db, request.user.user_id,
                    message.get('text'), message.get('chat_id')
                )

                update = {
                    "type": "new_group_msg",
                    "message": msg.to_dict(context={'mode': 'group'})
                }

                user_ids = await ChatRepository.get_users_in_chat(request.app.db, chat_id)

                await self.notify(request, user_ids, update)

            elif message.get('type') == 'new_private_msg':
                user_to = await UserRepository.by_id(request.app.db, message.get('to'))

                if not user_to:
                    request.app.logger.info('Private message to unknown user')
                    return

                if message.get('to') == request.user.user_id:  # TODO chat with yourself
                    return

                chat_id = await ChatRepository.get_private_chat_id(
                    request.app.db, [request.user.user_id, message.get('to')]
                )

                msg = await MessageRepository.create(
                    request.app.db, request.user.user_id,
                    message.get('text'), chat_id
                )

                update = {
                    "type": "new_private_msg",
                    "message": msg.to_dict(context={'mode': 'private', 'to': message.get('to')})
                }

                await self.notify(request, [request.user.user_id, message.get('to')], update)
            else:
                request.app.logger.info('Unknown message recieved: %s' % message)

    @staticmethod
    async def notify(request, user_ids, update):
        await request.app.msg_queue.put((update, user_ids))


class HistoryHandler:

    def __init__(self):
        pass

    async def handle_user_history(self, request):
        user_id = request.match_info['user_id']

        if user_id == request.user.user_id or not await UserRepository.by_id(request.app.db, user_id):
            raise web.HTTPForbidden

        chat_id = await ChatRepository.get_private_chat_id(request.app.db, [request.user.user_id, user_id])

        messages = await MessageRepository.load_all(request.app.db, chat_id)  # TODO pagination
        return web.json_response([msg.to_dict() for msg in messages])

    async def handle_chat_history(self, request):
        chat_id = request.match_info['chat_id']

        if not await ChatRepository.check_user_in_chat(request.app.db, chat_id, request.user.user_id):
            raise web.HTTPForbidden

        messages = await MessageRepository.load_all(request.app.db, chat_id)  # TODO pagination
        return web.json_response([msg.to_dict() for msg in messages])