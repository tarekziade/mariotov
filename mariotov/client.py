# see
# https://dxr.mozilla.org/mozilla-central/source/testing/marionette/driver.js#2971
import json
from asyncio import open_connection
from functools import partial


_PROTO = {'newSession': {'answer': True},
          'deleteSession': {'answer': True},
          'get': {'answer': False},
          'refresh': {'answer': False}}


class Marionette(object):
    def __init__(self, host='localhost', port=2828, loop=None):
        self.host = host
        self.port = port
        self.loop = loop
        self._r = self._w = None
        for command, options in _PROTO.items():
            func = partial(self.send, command, **options)
            setattr(self, command, func)

    async def __aenter__(self):
        await self.open()
        return self

    async def open(self):
        self._r, self._w = await open_connection(self.host, self.port,
                                                 loop=self.loop)
        await self.read()
        await self.newSession()

    async def close(self):
        await self.deleteSession()
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
        mid = 1
        message = [0, mid, command, options]
        message = json.dumps(message)
        message = '%d:%s' % (len(message), message)
        print(message)
        self._w.write(message.encode())

        if answer:
            data = await self.read()
            return data
