#!/usr/bin/python
# -*- coding: utf-8 -*-
# MeeGrid service (root) for the Nokia N9 (Harmattan PR1.3).
#
# Why root: the launcher (upstart job xsession/mthome) must be stopped while its
# layout files are replaced, otherwise it keeps the old layout in memory and
# writes it back. Killing it is not an option: the job has "respawn limit 3 300"
# and "reboot", so a few kills restart the phone. Only root may run initctl.
#
# The app (user `user`) writes one line into the FIFO /var/run/meegrid/cmd:
#   restore <id>    stop the launcher, copy the staged backup, start the launcher
#   backup <id>     make a backup (when the app cannot read the layout itself)
# and reads the result from /var/run/meegrid/status.json.
# Every hour it also runs the daily automatic backup (only if the layout changed).
# File work is done as user `user` through devel-su (root cannot read the
# launcher's files, and Aegis does not let root setuid).
#
# Runs from /etc/init/apps/meegrid-n9.conf (started by load-launcher after login).
# Designed and written by Claude (Anthropic) together with smyhu for Nokia N9. MIT licence.

import os
import sys
import json
import time
import errno
import select
import signal
import subprocess

VERSION = '0.1.2'
RUN_DIR = os.environ.get('MEEGRID_RUN', '/var/run/meegrid')
FIFO = os.path.join(RUN_DIR, 'cmd')
STATUS = os.path.join(RUN_DIR, 'status.json')
CORE = os.environ.get('MEEGRID_CORE', '/opt/meegrid-n9/core.py')
PYTHON = '/usr/bin/python'
JOB = os.environ.get('MEEGRID_JOB', 'xsession/mthome')
AUTO_EVERY = 900           # seconds between automatic backup checks
FIRST_AUTO = 600           # first check this long after start (boot is busy)

running = True


def log(msg):
    sys.stderr.write('meegridd: %s\n' % msg)
    sys.stderr.flush()


def as_user(args, timeout=60):
    """Runs core.py as user `user`. Returns (exit code, output)."""
    cmd = ' '.join([PYTHON, CORE] + args)
    if os.getuid() == 0:
        argv = ['devel-su', 'user', '-c', cmd]
    else:                                   # tests on a PC
        argv = ['sh', '-c', cmd]
    try:
        p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except OSError as e:
        return 127, str(e)
    end = time.time() + timeout
    while p.poll() is None and time.time() < end:
        time.sleep(0.2)
    if p.poll() is None:
        try:
            os.kill(p.pid, signal.SIGKILL)
        except OSError:
            pass
        return 124, 'timeout'
    return p.returncode, p.stdout.read().decode('utf-8', 'replace').strip()


def initctl(action):
    try:
        p = subprocess.Popen(['initctl', action, JOB], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = p.communicate()[0]
        return p.returncode, out.decode('utf-8', 'replace').strip()
    except OSError as e:
        return 127, str(e)


def launcher_running():
    code, out = initctl('status')
    return code == 0 and 'start/running' in out


def write_status(st):
    st['time'] = int(time.time())
    tmp = STATUS + '.tmp'
    f = open(tmp, 'w')
    try:
        f.write(json.dumps(st))
    finally:
        f.close()
    os.chmod(tmp, 0o644)
    os.rename(tmp, STATUS)


def do_restore(rid):
    write_status({'id': rid, 'cmd': 'restore', 'state': 'running'})
    code, out = initctl('stop')
    log('stop %s: %s %s' % (JOB, code, out))
    # "stop" returns once the job is stopped; give the process a moment to go
    time.sleep(1)
    try:
        code, out = as_user(['apply'])
        log('apply: %s %s' % (code, out))
    finally:
        scode, sout = initctl('start')
        log('start %s: %s %s' % (JOB, scode, sout))
        if not launcher_running():
            time.sleep(2)
            initctl('start')
    if code == 0:
        write_status({'id': rid, 'cmd': 'restore', 'state': 'done', 'file': out})
    else:
        write_status({'id': rid, 'cmd': 'restore', 'state': 'failed', 'error': out})


def do_backup(rid, kind):
    if kind not in ('manual', 'before'):
        kind = 'manual'
    write_status({'id': rid, 'cmd': 'backup', 'state': 'running'})
    code, out = as_user(['backup', kind])
    if code == 0:
        write_status({'id': rid, 'cmd': 'backup', 'state': 'done', 'file': out})
    else:
        write_status({'id': rid, 'cmd': 'backup', 'state': 'failed', 'error': out})


def handle(line):
    parts = line.strip().split()
    if not parts:
        return
    rid = parts[1][:40] if len(parts) > 1 else ''
    if parts[0] == 'restore':
        do_restore(rid)
    elif parts[0] == 'backup':
        do_backup(rid, parts[2] if len(parts) > 2 else 'manual')
    elif parts[0] == 'ping':
        write_status({'id': rid, 'cmd': 'ping', 'state': 'done', 'version': VERSION})
    else:
        log('unknown command: %r' % line[:80])


def setup_fifo():
    if not os.path.isdir(RUN_DIR):
        os.makedirs(RUN_DIR)
    os.chmod(RUN_DIR, 0o755)
    try:
        os.remove(FIFO)
    except OSError:
        pass
    os.mkfifo(FIFO)
    os.chmod(FIFO, 0o622)       # anyone may write a command, only root reads


def stop(*args):
    global running
    running = False


def main():
    signal.signal(signal.SIGTERM, stop)
    setup_fifo()
    write_status({'id': '', 'cmd': 'start', 'state': 'done', 'version': VERSION})
    # read end + our own write end: the FIFO never reports EOF between commands
    rfd = os.open(FIFO, os.O_RDONLY | os.O_NONBLOCK)
    wfd = os.open(FIFO, os.O_WRONLY)
    buf = b''
    next_auto = time.time() + FIRST_AUTO
    log('started %s' % VERSION)
    while running:
        wait = max(1, next_auto - time.time())
        try:
            r = select.select([rfd], [], [], wait)[0]
        except select.error as e:
            if e.args[0] == errno.EINTR:
                continue
            raise
        if r:
            try:
                chunk = os.read(rfd, 4096)
            except OSError as e:
                if e.errno in (errno.EAGAIN, errno.EINTR):
                    continue
                raise
            buf += chunk
            while b'\n' in buf:
                line, buf = buf.split(b'\n', 1)
                try:
                    handle(line.decode('utf-8', 'replace'))
                except Exception as e:
                    log('error: %s' % e)
            if len(buf) > 4096:
                buf = b''
        if time.time() >= next_auto:
            next_auto = time.time() + AUTO_EVERY
            code, out = as_user(['auto'])
            if out and out != '-':
                log('auto backup: %s %s' % (code, out))
    os.close(wfd)
    os.close(rfd)
    log('stopped')


if __name__ == '__main__':
    main()
