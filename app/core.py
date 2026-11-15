#!/usr/bin/python
# -*- coding: utf-8 -*-
# MeeGrid core - backup and restore of the Nokia N9 launcher icon layout.
# Runs as user `user` (from the app, or from the root service via devel-su).
# Python 2.6 (N9) and Python 3 (tests on a PC). No PySide here.
# Designed and written by Claude (Anthropic) together with smyhu for Nokia N9. MIT licence.
#
# What the launcher (meegotouchhome) keeps:
#   ~/.config/meegotouchhome-nokia/launcherbuttons.data   (INI, mode 600)
#       [DesktopEntries] <desktop file>=launcher/<folder>/<position>
#                                     or quicklaunchbar/<n>
#   ~/.local/share/applications/folderN.directory         (launcher folders)
#   ~/.local/share/applications/quicklaunchbarN.desktop   (quick launch bar copies)
#
# Backup = MyDocs/MeeGrid/meegrid-YYYYMMDD-HHMMSS-<kind>.tar.gz with those files
# plus meegrid.json (what was where, app names, installed packages).
#
# Command line (used by the root service meegridd.py):
#   core.py backup [manual|auto|before]   make a backup now
#   core.py auto                          daily automatic backup if due
#   core.py apply                         copy the staged backup into place
#                                         (the launcher must be stopped)

import os
import re
import sys
import json
import time
import shutil
import tarfile
import hashlib
import subprocess

VERSION = '0.1.2'
HOME = os.environ.get('MEEGRID_HOME', '/home/user')
DATA = os.path.join(HOME, '.config/meegotouchhome-nokia/launcherbuttons.data')
APPS = os.path.join(HOME, '.local/share/applications')
DOCS = os.path.join(HOME, 'MyDocs')
BACKUPS = os.path.join(DOCS, 'MeeGrid')
OWN = os.path.join(HOME, '.meegrid')
STAGE = os.path.join(OWN, 'stage')
SETTINGS = os.path.join(OWN, 'settings.json')
SYSTEM_APPS = os.environ.get('MEEGRID_SYSTEM_APPS', '/usr/share/applications')

KINDS = ('manual', 'auto', 'before')
BEFORE_KEEP = 5           # safety backups made before a restore
NAME_RE = re.compile(r'^meegrid-(\d{8})-(\d{6})-(manual|auto|before)\.tar\.gz$')
OWN_FILE_RE = re.compile(r'^(folder\d+\.directory|quicklaunchbar\d+\.desktop)$')


class Error(Exception):
    pass


def _read(path):
    f = open(path, 'rb')
    try:
        return f.read()
    finally:
        f.close()


def _write(path, data, mode=None):
    tmp = path + '.meegrid-tmp'
    f = open(tmp, 'wb')
    try:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    finally:
        f.close()
    if mode is not None:
        os.chmod(tmp, mode)
    os.rename(tmp, path)


def _text(b):
    if isinstance(b, bytes):
        return b.decode('utf-8', 'replace')
    return b


def _mkdirs(path):
    if not os.path.isdir(path):
        os.makedirs(path)


# ---------------------------------------------------------------- layout file

def _unescape_key(key):
    """QSettings INI key -> path. '\\' is the escaped '/', %XX and %UXXXX are
    escaped characters."""
    out = []
    i = 0
    while i < len(key):
        c = key[i]
        if c == '\\':
            out.append('/')
            i += 1
        elif c == '%' and key[i + 1:i + 2] == 'U' and len(key) >= i + 6:
            try:
                out.append(_unichr(int(key[i + 2:i + 6], 16)))
                i += 6
                continue
            except ValueError:
                out.append(c)
                i += 1
        elif c == '%' and len(key) >= i + 3:
            try:
                out.append(_unichr(int(key[i + 1:i + 3], 16)))
                i += 3
                continue
            except ValueError:
                out.append(c)
                i += 1
        else:
            out.append(c)
            i += 1
    return u''.join(out)


def _unichr(n):
    try:
        return unichr(n)
    except NameError:
        return chr(n)


def parse_layout(data):
    """Returns a list of {'path', 'where', 'folder', 'pos'} from the
    launcherbuttons.data contents (bytes)."""
    items = []
    section = None
    for line in _text(data).splitlines():
        line = line.strip()
        if not line or line.startswith(';') or line.startswith('#'):
            continue
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1]
            continue
        if '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = _unescape_key(key.strip())
        value = value.strip().strip('"')
        if section and section != 'DesktopEntries' and section != 'General':
            key = _unescape_key(section) + '/' + key
        if not key.endswith('.desktop') and not key.endswith('.directory'):
            continue
        if not key.startswith('/'):
            key = '/' + key
        parts = value.split('/')
        it = {'path': key, 'where': value, 'folder': -1, 'pos': -1}
        try:
            if parts[0] == 'launcher' and len(parts) >= 3:
                it['folder'] = int(parts[1])
                it['pos'] = int(parts[2])
            elif parts[0] == 'quicklaunchbar' and len(parts) >= 2:
                it['folder'] = -2
                it['pos'] = int(parts[1])
        except ValueError:
            pass
        items.append(it)
    return items


def parse_desktop(text, lang=None):
    """Name (translated if present) and Icon of a .desktop / .directory text."""
    name = loc = icon = u''
    in_entry = False
    for line in _text(text).splitlines():
        st = line.strip()
        if st.startswith('['):
            in_entry = st == '[Desktop Entry]'
            continue
        if not in_entry or '=' not in st:
            continue
        k, v = st.split('=', 1)
        k = k.strip()
        if k == 'Name':
            name = v.strip()
        elif lang and k == 'Name[%s]' % lang:
            loc = v.strip()
        elif k == 'Icon':
            icon = v.strip()
    return {'name': loc or name, 'icon': icon}


def desktop_name(path, lang=None):
    """Name= of a .desktop / .directory file (translated name if present)."""
    try:
        return parse_desktop(_read(path), lang)['name']
    except (IOError, OSError):
        return u''


ICON_DIRS = ('/usr/share/icons/hicolor/80x80/apps', '/usr/share/icons/hicolor/64x64/apps',
             '/usr/share/icons/hicolor/scalable/apps', '/usr/share/pixmaps')


def icon_url(icon):
    """Icon= value -> URL for QML Image (file, or the MeeGo theme provider)."""
    if not icon:
        return u''
    if icon.startswith('/'):
        return u'file://' + icon if os.path.exists(icon) else u''
    for d in ICON_DIRS:
        for ext in ('.png', '.svg', ''):
            p = os.path.join(d, icon + ext)
            if os.path.isfile(p):
                return u'file://' + p
    return u'image://theme/' + icon


def own_files():
    """Launcher's own files in ~/.local/share/applications."""
    try:
        names = os.listdir(APPS)
    except OSError:
        return []
    return sorted([n for n in names if OWN_FILE_RE.match(n)])


def installed_packages():
    try:
        p = subprocess.Popen(['dpkg-query', '-W', '-f', '${Package} ${Version} ${Status}\n'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = p.communicate()[0]
    except OSError:
        return []
    pk = []
    for line in _text(out).splitlines():
        f = line.split(' ', 2)
        if len(f) == 3 and f[2].endswith('installed') and 'not-installed' not in f[2]:
            pk.append(f[0] + ' ' + f[1])
    return pk


def describe(items, lang=None):
    """Adds app names, used for the list of missing apps after a reflash."""
    out = []
    for it in items:
        d = dict(it)
        try:
            info = parse_desktop(_read(it['path']), lang)
        except (IOError, OSError):
            info = {'name': u'', 'icon': u''}
        d['name'] = info['name'] or os.path.basename(it['path']).rsplit('.', 1)[0]
        d['icon'] = info['icon']
        out.append(d)
    return out


# ---------------------------------------------------------------- backups

def backup_name(kind, t=None):
    t = time.localtime(t or time.time())
    return 'meegrid-%s-%s.tar.gz' % (time.strftime('%Y%m%d-%H%M%S', t), kind)


def _add_bytes(tar, name, data, mtime):
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mtime = mtime
    info.mode = 0o644
    import io
    tar.addfile(info, io.BytesIO(data))


def make_backup(kind='manual', lang=None):
    """Creates a backup and returns its file name. Raises Error when the layout
    file cannot be read."""
    if kind not in KINDS:
        raise Error('bad kind')
    try:
        data = _read(DATA)
    except (IOError, OSError) as e:
        raise Error('errRead:' + str(e))
    items = describe(parse_layout(data), lang)
    files = own_files()
    now = int(time.time())
    meta = {
        'app': 'meegrid', 'version': VERSION, 'kind': kind, 'created': now,
        'md5': hashlib.md5(data).hexdigest(),
        'host': _hostname(),
        'items': items,
        'files': files,
        'folders': dict((f, desktop_name(os.path.join(APPS, f), lang)) for f in files
                        if f.startswith('folder')),
        'packages': installed_packages(),
    }
    _mkdirs(BACKUPS)
    name = backup_name(kind, now)
    path = os.path.join(BACKUPS, name)
    tmp = path + '.part'
    tar = tarfile.open(tmp, 'w:gz')
    try:
        _add_bytes(tar, 'meegrid.json', json.dumps(meta, indent=1, sort_keys=True).encode('utf-8'), now)
        _add_bytes(tar, 'launcherbuttons.data', data, now)
        for f in files:
            _add_bytes(tar, 'applications/' + f, _read(os.path.join(APPS, f)), now)
    finally:
        tar.close()
    os.rename(tmp, path)
    _prune()
    return name


def _hostname():
    try:
        return os.uname()[1]
    except Exception:
        return ''


def _prune():
    for kind, keep in (('auto', load_settings()['keep']), ('before', BEFORE_KEEP)):
        names = sorted([n for n in _names() if n.endswith('-%s.tar.gz' % kind)])
        for n in names[:-keep]:
            try:
                os.remove(os.path.join(BACKUPS, n))
            except OSError:
                pass


def _names():
    try:
        return [n for n in os.listdir(BACKUPS) if NAME_RE.match(n)]
    except OSError:
        return []


def read_meta(name):
    tar = tarfile.open(_backup_path(name), 'r:gz')
    try:
        m = tar.extractfile('meegrid.json')
        return json.loads(_text(m.read()))
    finally:
        tar.close()


def _backup_path(name):
    if not NAME_RE.match(name or ''):
        raise Error('bad name')
    return os.path.join(BACKUPS, name)


def missing_apps(meta):
    """Apps placed in the backup whose .desktop file is not on the phone now."""
    out = []
    for it in meta.get('items', []):
        p = it.get('path', '')
        base = os.path.basename(p)
        if OWN_FILE_RE.match(base):
            continue                       # restored together with the backup
        if os.path.exists(p):
            continue
        if p.startswith('/usr/share/applications/') and \
                os.path.exists(os.path.join(SYSTEM_APPS, p[len('/usr/share/applications/'):])):
            continue
        out.append(it.get('name') or base)
    return out


def list_backups():
    out = []
    for n in sorted(_names(), reverse=True):
        m = NAME_RE.match(n)
        e = {'file': n, 'kind': m.group(3),
             'date': '%s-%s-%s %s:%s' % (m.group(1)[:4], m.group(1)[4:6], m.group(1)[6:],
                                         m.group(2)[:2], m.group(2)[2:4]),
             'icons': 0, 'folders': 0, 'missing': [], 'ok': True}
        try:
            meta = read_meta(n)
            items = meta.get('items', [])
            e['icons'] = len([1 for i in items if i.get('path', '').endswith('.desktop')
                              and not OWN_FILE_RE.match(os.path.basename(i.get('path', '')))])
            e['folders'] = len([1 for f in meta.get('files', []) if f.startswith('folder')])
            e['missing'] = missing_apps(meta)
            e['host'] = meta.get('host', '')
        except Exception as ex:
            e['ok'] = False
            e['error'] = str(ex)
        out.append(e)
    return out


def _app_entry(path, lang, own, saved=None):
    """Name, icon and state of one launcher entry. `own` = folder / quick
    launch files taken from the backup itself."""
    base = os.path.basename(path)
    if base in own:
        d = parse_desktop(own[base], lang)
        missing = False
    else:
        exists = os.path.exists(path) or (path.startswith('/usr/share/applications/') and
                                           os.path.exists(os.path.join(SYSTEM_APPS, base)))
        if exists:
            try:
                d = parse_desktop(_read(path if os.path.exists(path) else os.path.join(SYSTEM_APPS, base)), lang)
            except (IOError, OSError):
                d = {'name': u'', 'icon': u''}
        else:
            # not on the phone now: name and icon as saved in the backup
            d = {'name': (saved or {}).get('name', u''), 'icon': (saved or {}).get('icon', u'')}
        missing = not exists
    return {'name': d['name'] or base.rsplit('.', 1)[0], 'icon': icon_url(d['icon']), 'missing': missing}


def preview(name, lang=None):
    """What the home screen of a backup looks like: main grid (apps and
    folders, in order), folder contents and the quick launch bar."""
    tar = tarfile.open(_backup_path(name), 'r:gz')
    try:
        own = {}
        data = None
        meta = {}
        for m in tar.getmembers():
            if not m.isfile():
                continue
            n = m.name[2:] if m.name.startswith('./') else m.name
            if n == 'launcherbuttons.data':
                data = tar.extractfile(m).read()
            elif n.startswith('applications/') and OWN_FILE_RE.match(n[13:]):
                own[n[13:]] = tar.extractfile(m).read()
            elif n == 'meegrid.json':
                try:
                    meta = json.loads(_text(tar.extractfile(m).read()))
                except ValueError:
                    meta = {}
    finally:
        tar.close()
    saved = dict((i.get('path'), i) for i in meta.get('items', []))
    if data is None:
        raise Error('errBroken')
    items = parse_layout(data)
    folders = {}            # folder number -> list of (pos, entry)
    grid = []
    bar = []
    for it in items:
        base = os.path.basename(it['path'])
        e = _app_entry(it['path'], lang, own, saved.get(it['path']))
        e['pos'] = it['pos']
        fm = re.match(r'^folder(\d+)\.directory$', base)
        if fm and it['folder'] == 0:
            e['type'] = 'folder'
            e['folder'] = int(fm.group(1))
            grid.append(e)
        elif it['folder'] == -2:
            e['type'] = 'app'
            bar.append(e)
        elif it['folder'] == 0:
            e['type'] = 'app'
            grid.append(e)
        elif it['folder'] > 0:
            e['type'] = 'app'
            folders.setdefault(it['folder'], []).append(e)
    key = lambda e: e['pos']
    grid.sort(key=key)
    bar.sort(key=key)
    out_folders = []
    for e in grid:
        if e['type'] == 'folder':
            content = sorted(folders.pop(e['folder'], []), key=key)
            e['items'] = content
            e['thumbs'] = [c['icon'] for c in content[:4]]
            e['missing'] = False
            out_folders.append({'name': e['name'], 'items': content})
    # entries in folders that have no folder icon on the grid (should not happen)
    for f in sorted(folders):
        out_folders.append({'name': u'#%d' % f, 'items': sorted(folders[f], key=key)})
    return {'grid': grid, 'bar': bar, 'folders': out_folders}


THUMBS = os.path.join(OWN, 'thumbs')


def thumbnail(name, lang=None, count=16):
    """First icons of the main grid, for the small preview in the list
    (cached in ~/.meegrid/thumbs)."""
    cache = os.path.join(THUMBS, name + '.json')
    try:
        return json.loads(_text(_read(cache)))
    except Exception:
        pass
    p = preview(name, lang)
    out = []
    for e in p['grid'][:count]:
        out.append({'icon': e['icon'], 'folder': e['type'] == 'folder', 'thumbs': e.get('thumbs', []),
                    'missing': e['missing']})
    try:
        _mkdirs(THUMBS)
        _write(cache, json.dumps(out).encode('utf-8'))
    except (IOError, OSError):
        pass
    return out


def delete_backup(name):
    os.remove(_backup_path(name))
    try:
        os.remove(os.path.join(THUMBS, name + '.json'))
    except OSError:
        pass


# ---------------------------------------------------------------- automatic

DEFAULTS = {'auto': True,   # automatic backup on/off
            'every': 1,     # days between automatic backups: 1 or 7
            'hour': 3,      # at this hour (or at the first check after it)
            'keep': 10,     # automatic backups kept; older ones are deleted
            'skip': 0,      # planned time of one skipped automatic backup (0 = none)
            'since': 0}     # when automatic backups were switched on (first one at the next planned hour)
DAY = 24 * 3600


def load_settings():
    s = dict(DEFAULTS)
    try:
        f = json.loads(_text(_read(SETTINGS)))
        if isinstance(f, dict):
            for k in DEFAULTS:
                if k in f:
                    s[k] = f[k]
    except Exception:
        pass
    try:
        s['every'] = 7 if int(s['every']) == 7 else 1
        s['hour'] = min(23, max(0, int(s['hour'])))
        s['keep'] = min(100, max(1, int(s['keep'])))
        s['skip'] = int(s['skip'])
        s['since'] = int(s['since'])
    except (TypeError, ValueError):
        return dict(DEFAULTS)
    s['auto'] = bool(s['auto'])
    return s


def save_settings(changes):
    s = load_settings()
    if 'auto' in changes and bool(changes['auto']) != s['auto']:
        changes = dict(changes)
        changes['since'] = int(time.time()) if changes['auto'] else 0
        changes['skip'] = 0
    for k in DEFAULTS:
        if k in changes:
            s[k] = changes[k]
    _mkdirs(OWN)
    _write(SETTINGS, json.dumps(s).encode('utf-8'))
    return load_settings()


def auto_enabled():
    return load_settings()['auto']


def set_auto(on):
    save_settings({'auto': bool(on)})


def _name_time(n):
    m = NAME_RE.match(n)
    return time.mktime(time.strptime(m.group(1) + m.group(2), '%Y%m%d%H%M%S'))


def last_auto():
    autos = sorted([n for n in _names() if n.endswith('-auto.tar.gz')])
    return _name_time(autos[-1]) if autos else 0


def due_time(s, last, now):
    """When the next automatic backup is due (local time)."""
    lt = time.localtime(now)
    slot = time.mktime((lt[0], lt[1], lt[2], s['hour'], 0, 0, 0, 0, -1))
    if slot > now:
        slot -= DAY
    # slot = the latest planned hour that has already passed; a backup made
    # late (phone was off) does not push the next one by a whole period
    gap = s['every'] * DAY - 12 * 3600 if s['every'] > 1 else 1
    if slot - last >= gap:
        return slot                      # due now
    nxt = slot + DAY
    while nxt - last < gap:
        nxt += DAY
    return nxt


def _effective_last(s, now=None):
    # a skipped backup counts as made at its planned time; before the first
    # automatic backup we count from the moment they were switched on
    return max(last_auto(), s.get('skip', 0), s.get('since', 0) or now or time.time())


def auto_info(now=None):
    now = now or time.time()
    s = load_settings()
    if s['auto'] and not s['since']:
        s = save_settings({'since': int(now)})
    last = last_auto()
    nxt = int(max(now, due_time(s, _effective_last(s, now), now)))
    autos = len([n for n in _names() if n.endswith('-auto.tar.gz')])
    return {'settings': s, 'last': int(last), 'next': nxt, 'skipped': s['skip'] > 0 and s['skip'] > last,
            'count': autos, 'would_delete': max(0, autos + 1 - s['keep'])}


def skip_next(now=None):
    """Skips the next planned automatic backup."""
    now = now or time.time()
    s = load_settings()
    return save_settings({'skip': int(due_time(s, _effective_last(s, now), now))})


def unskip():
    return save_settings({'skip': 0})


def auto_backup(now=None):
    """Automatic backup when due, and only when the layout changed since the
    newest backup. Returns the file name or None."""
    s = load_settings()
    if not s['auto']:
        return None
    now = now or time.time()
    if not s['since']:
        save_settings({'since': int(now)})
        return None
    if due_time(s, _effective_last(s, now), now) > now:
        return None
    try:
        cur = hashlib.md5(_read(DATA)).hexdigest()
    except (IOError, OSError):
        return None
    newest = sorted(_names(), key=lambda n: n[8:23])
    if newest:
        try:
            if read_meta(newest[-1]).get('md5') == cur:
                return None
        except Exception:
            pass
    return make_backup('auto')


# ---------------------------------------------------------------- restore

def stage(name):
    """Unpacks a backup into ~/.meegrid/stage (only the files we know)."""
    tar = tarfile.open(_backup_path(name), 'r:gz')
    try:
        if os.path.isdir(STAGE):
            shutil.rmtree(STAGE)
        os.makedirs(os.path.join(STAGE, 'applications'))
        got = False
        for m in tar.getmembers():
            if not m.isfile():
                continue
            n = m.name
            if n.startswith('./'):
                n = n[2:]
            if n == 'launcherbuttons.data':
                dst = os.path.join(STAGE, n)
                got = True
            elif n.startswith('applications/') and OWN_FILE_RE.match(n[len('applications/'):]):
                dst = os.path.join(STAGE, n)
            elif n == 'meegrid.json':
                dst = os.path.join(STAGE, n)
            else:
                continue
            _write(dst, tar.extractfile(m).read(), 0o600)
        if not got:
            raise Error('errBroken')
    finally:
        tar.close()
    _write(os.path.join(STAGE, 'READY'), name.encode('utf-8'))


def apply_stage():
    """Copies the staged files into place. Call only with the launcher stopped."""
    ready = os.path.join(STAGE, 'READY')
    if not os.path.exists(ready):
        raise Error('errNoStage')
    data = _read(os.path.join(STAGE, 'launcherbuttons.data'))
    if not data.strip() or b'[' not in data:
        raise Error('errBroken')
    _mkdirs(APPS)
    _mkdirs(os.path.dirname(DATA))
    staged = sorted(os.listdir(os.path.join(STAGE, 'applications')))
    for f in own_files():
        if f not in staged:
            os.remove(os.path.join(APPS, f))
    for f in staged:
        if OWN_FILE_RE.match(f):
            _write(os.path.join(APPS, f), _read(os.path.join(STAGE, 'applications', f)), 0o644)
    _write(DATA, data, 0o600)
    name = _text(_read(ready))
    shutil.rmtree(STAGE)
    return name


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ''
    try:
        if cmd == 'backup':
            print(make_backup(argv[2] if len(argv) > 2 else 'manual'))
        elif cmd == 'auto':
            print(auto_backup() or '-')
        elif cmd == 'apply':
            print(apply_stage())
        elif cmd == 'list':
            print(json.dumps(list_backups(), indent=1))
        else:
            sys.stderr.write('usage: core.py backup [manual|auto|before] | auto | apply | list\n')
            return 2
    except Error as e:
        sys.stderr.write('meegrid: %s\n' % e)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
