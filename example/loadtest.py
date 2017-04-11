import os
from mariotov import setup          # NOQA
from molotov import scenario


_HERE = os.path.dirname(__file__)


@scenario(100)
async def test(session):
    browser = session.browser
    url = os.path.join(_HERE, 'test.html')
    url2 = os.path.join(_HERE, 'test2.html')
    await browser.get(url=url)
    await browser.refresh()
    await browser.get(url=url2)
