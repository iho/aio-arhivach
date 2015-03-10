#!/usr/bin/env python
# coding: utf-8

# from __future__ import division, print_function, unicode_literals
import datetime
import os
import random
import string
from urllib.parse import urlparse

import aiohttp
import ipaddress
from aiohttp import web
from aiopg.sa import create_engine
from lxml.html import fromstring, tostring

import asyncio
from models import Page

all_chars = string.digits + string.ascii_lowercase + string.ascii_uppercase


def gen_hash(length=5):
    return ''.join(random.choice(all_chars) for x in range(length))

with open('form.html') as file:
    string = file.read().encode('utf-8')


@asyncio.coroutine
def index(request):
    return web.Response(body=string)


sem = asyncio.Semaphore(5)
Page = Page.__table__


@asyncio.coroutine
def index_post(request):
    yield from request.post()
    url = request.POST['url']
    if not (url.startswith('http://') or url.startswith('https://')):
        url = 'http://' + url
    print(url)
    ip_ = request.transport.get_extra_info('peername')[0]
    ip = ipaddress.ip_address(ip_)
    time = datetime.datetime.now().time()
    if ip:
        with (yield from sem):
            r = yield from aiohttp.request('get', url)
        raw = yield from r.text()
        url_ = url
        url = urlparse(url)
        base_url = url.scheme + '://' + url.netloc
        xpath_tree = fromstring(raw)
        xpath_tree.make_links_absolute(base_url=base_url)
        raw = tostring(xpath_tree).decode('utf-8')
        name = gen_hash()

        query = Page.insert().values(
            key=name,
            ip=ip_,
            url=url_,
            body=raw
        )
        with (yield from request.app['database']) as conn:
            yield from conn.execute(query)
        return aiohttp.web.HTTPFound('/' + name)
    return web.Response(body="Error")


@asyncio.coroutine
def page(request):
    name = request.match_info.get('name', None)
    if name:

        query = Page.select().where(Page.c.key == name)
        with (yield from request.app['database']) as conn:
            res = yield from conn.execute(query)
            res = yield from res.first()

        if res:
            body = res['body'].encode('utf-8')
            return web.Response(body=body)
    return web.HTTPNotFound()


def parse_uri(uri):
    from urllib.parse import urlparse
    uri = urlparse(uri)
    return dict(
        user=uri.username,
        password=uri.password,
        database=uri.path[1:],
        port=str(uri.port),
        host=uri.hostname
    )


@asyncio.coroutine
def init(loop=None):
    #    loop = loop or asyncio.get_event_loop()
    app = aiohttp.web.Application(loop=loop)

    uri = os.environ.get('DATABASE_URL')
    default_uri = dict(user='aiopg',
                       database='aiopg',
                       host='127.0.0.1',
                       port='5433',
                       password='passwd')
    uri = parse_uri(uri) if uri else default_uri
    engine = yield from create_engine(**uri)

    app['database'] = engine
    app.router.add_route('GET', '/', index)
    app.router.add_route('POST', '/', index_post)
    app.router.add_route('GET', '/{name}', page)
    handler = app.make_handler()
    PORT = os.environ.get('PORT', '8881')
    srv = yield from loop.create_server(handler,
                                        '0.0.0.0', int(PORT))
    print("Server started at http://127.0.0.1:" + PORT)
    return srv,  handler


@asyncio.coroutine
def finish(srv,  handler):
    srv.close()
    yield from handler.finish_connections()
    yield from srv.wait_closed()
if __name__ == '__main__':
    #    asyncio.async(asyncio.gather(*run()))
    loop = asyncio.get_event_loop()
#    log.info('Server start')

    srv,  handler = loop.run_until_complete(init(loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(finish(srv,  handler))
        loop.stop()
       # log.info('Server stoped')
