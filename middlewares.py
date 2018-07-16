from aiohttp import web

from repositories import UserRepository


@web.middleware
async def check_auth(request, handler):
    if request.match_info.route.name not in ['register', 'login']:
        if not request.user:
            raise web.HTTPForbidden

    return await handler(request)


@web.middleware
async def set_user(request, handler):
    request.user = await UserRepository.get_user_from_request(request)

    return await handler(request)