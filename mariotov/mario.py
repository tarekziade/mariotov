# see
# https://dxr.mozilla.org/mozilla-central/source/testing/marionette/driver.js#2971
import os
import functools
import asyncio

from mariotov.client import Marionette
from mariotov.util import start_firefox, stop_firefox, get_marionette_port
from molotov import (setup, teardown, session_setup, session_teardown,
                     scenario)


_HERE = os.path.dirname(__file__)


@setup()
async def setup_worker(worker_id, args):
    loop = asyncio.get_event_loop()
    start_ff = functools.partial(start_firefox, worker_id)
    await loop.run_in_executor(None, start_ff)


@teardown()
def teardown_worker(worker_id):
    stop_firefox(worker_id)


@session_setup()
async def setup_session(worker_id, session):
    port = get_marionette_port(worker_id)
    session.browser = Marionette(loop=session.loop, port=port)
    await session.browser.open()


@session_teardown()
async def teardown_session(worker_id, session):
    await session.browser.close()


@scenario(100)
async def test(session):
    browser = session.browser
    url = os.path.join(_HERE, 'test.html')
    url2 = os.path.join(_HERE, 'test2.html')
    await browser.get(url=url)
    await browser.refresh()
    await browser.get(url=url2)
