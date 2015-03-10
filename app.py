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

from lxml import etree
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
utf8_parser = etree.HTMLParser(encoding='utf-8')

def parse_from_unicode(unicode_str):
    s = unicode_str.encode('utf-8')
    return fromstring(s, parser=utf8_parser)

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
#        raw_ = raw
 #       raw = raw.encode('utf-8')
        url_ = url
        url = urlparse(url)
        base_url = url.scheme + '://' + url.netloc
        xpath_tree_old = fromstring(raw)
        xpath_tree = parse_from_unicode(raw)
        import ipdb; ipdb.set_trace()   
        xpath_tree.make_links_absolute(base_url=url)
        raw = tostring(xpath_tree)
        name = gen_hash()
        import ipdb; ipdb.set_trace()

        query = Page.insert().values(
            key=name,
            ip=ip_,
            url=url_,
            body=str(raw)
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
            body = res['body']
            return web.Response(text=body)
    return web.HTTPNotFound()


@asyncio.coroutine
def init(loop=None):
    #    loop = loop or asyncio.get_event_loop()
    app = aiohttp.web.Application(loop=loop)

    engine = yield from create_engine(user='aiopg',
                                      database='aiopg',
                                      host='127.0.0.1',
                                      port='5433',
                                      password='passwd')

    app['database'] = engine
    app.router.add_route('GET', '/', index)
    app.router.add_route('POST', '/', index_post)
    app.router.add_route('GET', '/{name}', page)
    handler = app.make_handler()
    PORT = os.environ['PORT']
    srv = yield from loop.create_server(handler,
                                        '127.0.0.1', int(PORT))
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
# environ.get('DATABASE_URL')
# furl.furl

# In[2]:
#     from urllib.parse import urlparse


# In[13]:
#     ss.username
# Out[13]:
#     'aiopg'

# In[14]:
#     ss.host
# Out[14]:
#     'localhost'

# In[15]:
#     ss.password
# Out[15]:
#     'passwd'


# In[17]:
#     ss.path
# Out[17]:
#     Path('/aiopg')

# In[18]:
#     ss.port
# Out[18]:
#     5433

# (user='aiopg',
#  database='aiopg',
#  host='127.0.0.1',
#  port='5433',
#  password='passwd')
