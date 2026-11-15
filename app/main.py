#!/usr/bin/python
# -*- coding: utf-8 -*-
# MeeGrid - backup and restore of the Nokia N9 launcher icon layout.
# Python 2.6 + PySide + QML. Restoring goes through the root service meegridd
# (it stops and starts the launcher).
# Designed and written by Claude (Anthropic) together with smyhu for Nokia N9. MIT licence.

import os
import sys
import json
import time
import random
import subprocess

from PySide.QtCore import QObject, QUrl, Slot
from PySide.QtGui import QApplication
from PySide.QtDeclarative import QDeclarativeView

APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)
import core

APP_VERSION = '0.1.2'
BUS_NAME = 'com.github.smyhu.meegrid'
LANGUAGES = ('pl', 'en')
FIFO = '/var/run/meegrid/cmd'
STATUS = '/var/run/meegrid/status.json'


def session_env():
    if not os.environ.get('DBUS_SESSION_BUS_ADDRESS'):
        try:
            for line in open('/tmp/session_bus_address.user').read().splitlines():
                line = line.strip()
                if line.startswith('export '):
                    line = line[7:]
                if line.startswith('DBUS_SESSION_BUS_ADDRESS='):
                    os.environ['DBUS_SESSION_BUS_ADDRESS'] = line.split('=', 1)[1].strip("'\"")
        except IOError:
            pass


def phone_language():
    code = os.environ.get('MEEGRID_LANG', '')
    if not code:
        session_env()
        try:
            p = subprocess.Popen(['gconftool-2', '-g', '/meegotouch/i18n/language'],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            code = p.communicate()[0].strip()
        except OSError:
            pass
    code = (code or os.environ.get('LANG', ''))[:2].lower()
    return code if code in LANGUAGES else 'en'


def js(obj):
    return unicode(json.dumps(obj))


def u(e):
    return unicode(str(e), 'utf-8', 'replace')


def send(verb, arg=''):
    """One command line to the root service. Returns the request id or ''."""
    if not os.path.exists(FIFO):
        return ''
    rid = '%d%04d' % (int(time.time()), random.randint(0, 9999))
    try:
        fd = os.open(FIFO, os.O_WRONLY | os.O_NONBLOCK)
    except OSError:
        return ''
    try:
        os.write(fd, ('%s %s %s' % (verb, rid, arg)).strip() + '\n')
    finally:
        os.close(fd)
    return rid


class Backend(QObject):
    """QML gets everything as JSON text (PySide 1.0.7 cannot pass Python
    dicts or signal arguments to QML)."""

    def __init__(self, lang):
        QObject.__init__(self)
        self.lang = lang

    @Slot(result=unicode)
    def backups(self):
        try:
            return js({'ok': True, 'items': core.list_backups(), 'service': os.path.exists(FIFO)})
        except Exception, e:
            return js({'ok': False, 'error': u(e)})

    @Slot(result=unicode)
    def backupNow(self):
        """Direct backup; if the app cannot read the launcher file, asks the service."""
        try:
            return js({'ok': True, 'file': core.make_backup('manual', self.lang)})
        except core.Error, e:
            if not str(e).startswith('errRead'):
                return js({'ok': False, 'error': u(e)})
            rid = send('backup', 'manual')
            if rid:
                return js({'ok': True, 'wait': rid})
            return js({'ok': False, 'error': 'errNoService'})
        except Exception, e:
            return js({'ok': False, 'error': u(e)})

    @Slot(unicode, result=unicode)
    def restore(self, name):
        name = name.encode('utf-8')
        if not os.path.exists(FIFO):
            return js({'ok': False, 'error': 'errNoService'})
        try:
            core.stage(name)
        except Exception, e:
            return js({'ok': False, 'error': u(e)})
        safety = ''
        try:
            safety = core.make_backup('before', self.lang)
        except Exception, e:
            print 'meegrid: no safety backup:', e
        rid = send('restore')
        if not rid:
            return js({'ok': False, 'error': 'errNoService'})
        return js({'ok': True, 'wait': rid, 'safety': safety})

    @Slot(unicode, result=unicode)
    def thumb(self, name):
        try:
            return js(core.thumbnail(name.encode('utf-8'), self.lang))
        except Exception, e:
            return js([])

    @Slot(unicode, result=unicode)
    def preview(self, name):
        try:
            p = core.preview(name.encode('utf-8'), self.lang)
            p['ok'] = True
            return js(p)
        except Exception, e:
            return js({'ok': False, 'error': u(e)})

    @Slot(unicode, result=unicode)
    def status(self, rid):
        try:
            st = json.loads(open(STATUS).read())
        except Exception:
            return js({'state': 'waiting'})
        if st.get('id') != rid:
            return js({'state': 'waiting'})
        return js(st)

    @Slot(unicode, result=unicode)
    def details(self, name):
        try:
            meta = core.read_meta(name.encode('utf-8'))
            return js({'ok': True, 'missing': core.missing_apps(meta),
                       'packages': len(meta.get('packages', [])), 'host': meta.get('host', ''),
                       'folders': sorted([v for v in meta.get('folders', {}).values() if v])})
        except Exception, e:
            return js({'ok': False, 'error': u(e)})

    @Slot(unicode, result=unicode)
    def remove(self, name):
        try:
            core.delete_backup(name.encode('utf-8'))
            return js({'ok': True})
        except Exception, e:
            return js({'ok': False, 'error': u(e)})

    @Slot(result=unicode)
    def settings(self):
        """Settings + last and next automatic backup (local time, for QML)."""
        try:
            i = core.auto_info()
        except Exception, e:
            return js({'ok': False, 'error': u(e)})
        fmt = lambda t: time.strftime('%Y-%m-%d %H:%M', time.localtime(t)) if t else ''
        return js({'ok': True, 'settings': i['settings'], 'last': fmt(i['last']), 'next': fmt(i['next']),
                   'skipped': i['skipped'], 'skippedAt': fmt(i['settings']['skip']),
                   'count': i['count'], 'wouldDelete': i['would_delete']})

    @Slot(bool, result=unicode)
    def skipNext(self, on):
        try:
            if on:
                core.skip_next()
            else:
                core.unskip()
        except Exception, e:
            return js({'ok': False, 'error': u(e)})
        return self.settings()

    @Slot(unicode, result=unicode)
    def saveSettings(self, text):
        try:
            core.save_settings(json.loads(text))
        except Exception, e:
            return js({'ok': False, 'error': u(e)})
        return self.settings()


class Window(object):
    """Only one copy of the app; a second start brings the first to the front."""

    def __init__(self):
        self.view = None
        self.bus = None
        try:
            import dbus
            import dbus.service
            from dbus.mainloop.glib import DBusGMainLoop
        except ImportError, e:
            print 'meegrid: no D-Bus:', e
            return
        DBusGMainLoop(set_as_default=True)
        session_env()
        bus = dbus.SessionBus()
        if bus.request_name(BUS_NAME, dbus.bus.NAME_FLAG_DO_NOT_QUEUE) != dbus.bus.REQUEST_NAME_REPLY_PRIMARY_OWNER:
            self.bus = bus
            return
        owner = self

        class Service(dbus.service.Object):
            @dbus.service.method(BUS_NAME, in_signature='', out_signature='')
            def top(self):
                owner.top()

        self.service = Service(bus, '/')

    def running_elsewhere(self):
        if not self.bus:
            return False
        try:
            self.bus.get_object(BUS_NAME, '/').top(dbus_interface=BUS_NAME)
        except Exception, e:
            print 'meegrid: cannot reach the running copy:', e
        return True

    def top(self):
        if self.view:
            self.view.showFullScreen()
            self.view.raise_()
            self.view.activateWindow()


def main():
    os.environ.setdefault('DISPLAY', ':0')
    app = QApplication(sys.argv)
    app.setApplicationName('meegrid')
    app.setOrganizationName('meegrid')
    window = Window()
    if window.running_elsewhere():
        return
    lang = phone_language()
    view = QDeclarativeView()
    backend = Backend(lang)
    ctx = view.rootContext()
    ctx.setContextProperty('uiLang', lang)
    ctx.setContextProperty('appVersion', APP_VERSION)
    ctx.setContextProperty('backend', backend)
    view.setResizeMode(QDeclarativeView.SizeRootObjectToView)
    view.setSource(QUrl.fromLocalFile(os.path.join(APP_DIR, 'qml', 'main.qml')))
    view.showFullScreen()
    window.view = view
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
