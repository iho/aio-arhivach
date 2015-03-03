#!/usr/bin/env python
# coding: utf-8

# from __future__ import division, print_function, unicode_literals
import datetime
import random
import string
from urllib.parse import urlparse

import aiohttp
import aioredis
import ipaddress
from aiohttp import web

import asyncio

all_chars = string.digits + string.ascii_lowercase + string.ascii_uppercase


def gen_hash(length=5):
    return ''.join(random.choice(all_chars) for x in range(length))

with open('form.html') as file:
    string = file.read().encode('utf-8')


@asyncio.coroutine
def index(request):
    return web.Response(body=string)


sem = asyncio.Semaphore(5)


@asyncio.coroutine
def index_post(request):
    "Add block for too much gets from one IP"
    "Replace all urls to absolute by lxml"
    "Add html with link on original"
    yield from request.post()
    url = request.POST['url']
    if not (url.startswith('http://') or url.startswith('https://')):
        url = 'http://' + url
    print(url)
    ip = request.transport.get_extra_info('peername')[0]
    ip = ipaddress.ip_address(ip)
    time = datetime.datetime.now().time()
    if ip:
        with (yield from sem):
            r = yield from aiohttp.request('get', url)
        raw = yield from r.text()
        name = gen_hash()
        yield from redis.set("saved_pages#" + name, raw)
        return aiohttp.web.HTTPFound('/' + name)
    return web.Response(body="Error")


@asyncio.coroutine
def page(request):
    name = request.match_info.get('name', None)
    if name:
        body = yield from redis.get("saved_pages#" + name)
        if body:
            return web.Response(body=body)
    return web.HTTPNotFound()


@asyncio.coroutine
def init(loop=None):
    #    loop = loop or asyncio.get_event_loop()
    app = aiohttp.web.Application(loop=loop)
    redis = yield from aioredis.create_redis(
        ('localhost', 6379), loop=loop)

    app.redis = redis

    app.router.add_route('GET', '/', index)
    app.router.add_route('POST', '/', index_post)
    app.router.add_route('GET', '/{name}', page)
    handler = app.make_handler()

    srv = yield from loop.create_server(handler,
                                        '127.0.0.1', 8080)
    print("Server started at http://127.0.0.1:8080")
    return srv, redis, handler


@asyncio.coroutine
def finish(srv, redis, handler):
    redis.close()
    srv.close()
    yield from handler.finish_connections()
    yield from srv.wait_closed()

if __name__ == '__main__':
    #    asyncio.async(asyncio.gather(*run()))
    loop = asyncio.get_event_loop()
#    log.info('Server start')

    srv, redis, handler = loop.run_until_complete(init(loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(finish(srv, redis, handler))
        loop.stop()
       # log.info('Server stoped')
