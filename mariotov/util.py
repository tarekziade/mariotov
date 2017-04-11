import os
import shlex
import subprocess
import time
import socket


_WORKDIR = '/tmp'
_HERE = os.path.dirname(__file__)
_USER_JS = os.path.join(_HERE, 'user.js')
_RUN_FF = '/Applications/FirefoxNightly.app/Contents/MacOS/firefox'
_FF_OPTIONS = '--marionette -new-instance --profile %s'
_P = {}


def _get_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    finally:
        s.close()
    return port


def get_marionette_port(worker_id):
    return _P[worker_id][0]


def start_firefox(worker_id):
    pref_dir = os.path.join(_WORKDIR, 'worker-%d' % worker_id)
    if not os.path.exists(pref_dir):
        os.mkdir(pref_dir)

    port = _get_port()
    user_js = os.path.join(pref_dir, 'user.js')
    with open(user_js, 'w') as target:
        with open(_USER_JS) as source:
            content = source.read() % {'port': port}
            target.write(content)

    args = shlex.split(_RUN_FF + ' ' + _FF_OPTIONS % pref_dir)
    _P[worker_id] = port, subprocess.Popen(args, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
    # XXX should listen to the socket instead, until it's ready
    time.sleep(5)
    return port


def stop_firefox(worker_id):
    _P[worker_id][1].terminate()
