# see
# https://dxr.mozilla.org/mozilla-central/source/testing/marionette/driver.js#2971
import os
import shlex
import subprocess
import functools
import json
from asyncio import open_connection
import asyncio
import subprocess
import time
from uuid import uuid4
import socket

from molotov import *


class Marionette(object):
    def __init__(self, host='localhost', port=2828, loop=None):
        self.host = host
        self.port = port
        self.loop = loop
        self._r = self._w = None

    async def __aenter__(self):
        await self.open()
        return self

    async def open(self):
        self._r, self._w = await open_connection(self.host, self.port,
                                                 loop=self.loop)
        await self.read()
        await self('newSession')

    async def close(self):
        await self('deleteSession')
        self._w.close()
        self._r = self._w = None

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def read(self):
        reader = self._r
        size = (await reader.readuntil(b':')).decode()
        size = int(size[:-1])
        data = (await reader.readexactly(size)).decode()
        return json.loads(data)

    async def send(self, command, **options):
        answer = options.pop('answer', True)
        print('->', command, str(options))
        mid = 1
        message = [0, mid, command, options]
        message = json.dumps(message)
        message = '%d:%s' % (len(message), message)
        self._w.write(message.encode())

        if answer:
            data = await self.read()
            return data

    __call__ = send



_RUN_FF = '/Applications/FirefoxNightly.app/Contents/MacOS/firefox'
_FF_OPTIONS = '--marionette -new-instance --profile worker-%d'
_P = {}


def get_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("",0))
        s.listen(1)
        port = s.getsockname()[1]
    finally:
        s.close()
    return port


def _start_ff(worker_id):
    pref_dir = 'worker-%d' % worker_id
    if not os.path.exists(pref_dir):
        os.mkdir(pref_dir)

    port = get_port()
    user_js = os.path.join(pref_dir, 'user.js')
    with open(user_js, 'w') as target:
        with open('user.js') as source:
            content = source.read() % {'port': port}
            target.write(content)

    # XXX
    # 'worker-%d' % worker_id
    # we want to create the profile dir in order to set up
    # the port marionette listens to in the prefs,
    # so we can have several FF instances
    args = shlex.split(_RUN_FF + ' ' + _FF_OPTIONS % worker_id)
    _P[worker_id] = port, subprocess.Popen(args, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    # XXX should listen to the socket instead, until it's ready
    time.sleep(5)


@setup()
async def _setup_worker(worker_id, args):
    loop = asyncio.get_event_loop()
    start_ff = functools.partial(_start_ff, worker_id)
    await loop.run_in_executor(None, start_ff)


@teardown()
def _bye(worker_id):
    _P[worker_id][1].terminate()


@session_setup()
async def _setup(worker_id, session):
    port = _P[worker_id][0]
    session.browser = Marionette(loop=session.loop, port=port)
    await session.browser.open()


@session_teardown()
async def _teardown(worker_id, session):
    await session.browser.close()


@scenario(100)
async def test(session):
    url = 'file:///Users/tarek/Dev/github.com/mariotov/test.html'
    url2 = 'file:///Users/tarek/Dev/github.com/mariotov/test2.html'
    await session.browser('get', url=url, answer=False)
    #print(await session.browser('getCurrentUrl'))
    #await session.browser('refresh', answer=False)
    await session.browser('get', url=url2, answer=False)
    #await session.browser('goBack', answer=False)
    #print(await session.browser('getCurrentUrl'))
    #resp = await session.browser('get', url=url2)
