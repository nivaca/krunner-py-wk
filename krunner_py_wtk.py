#!/usr/bin/env python3
"""py-wtk in KRunner: type "wtk rosa" (or "wtk rosa @la") and the entries
of the English Wiktionary appear.

A D-Bus runner (the interface org.kde.krunner1): KRunner calls Match for
each query (see the .desktop file that install.py writes), and Run when a
match is chosen.  D-Bus starts this program the first time it is needed;
it stays, with py-wtk loaded.

    python3 krunner_py_wtk.py [--py-wtk FOLDER]

Wiktionary is on the network, so Match answers when it can: at once if the
query was answered a moment ago, else after a short pause in the typing
(a query replaced by the next keystroke is never sent), on a thread, so
that KRunner is not kept waiting.  The pages stay in py-wtk's disk cache.

Enter opens the entry in the window of py-wtk (py-wtk-gui, in that
language); the actions copy the entry, open it on Wiktionary, and open the
settings of the runner (settings_dialog.py).  "wtk ?" (or "wtk settings")
gives a single match that opens the settings.  Needs python3-dbus and
python3-gobject.
"""

import argparse
import glob
import html
import os
import shutil
import subprocess
import sys
import threading
import webbrowser

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

import lookup
import runner_settings

VERSION = '1.0'
SERVICE = 'io.github.nivaca.PyWtkKRunner'
PATH = '/runner'
IFACE = 'org.kde.krunner1'
#  What starts a query, as usual (the settings can change it): wtk rosa
PREFIX = runner_settings.PREFIX
CATEGORY = 'py-wtk'
#  KRunner's types of match (KRunner::QueryMatch::CategoryRelevance)
EXACT = 100
POSSIBLE = 30
#  The pause in the typing (ms) after which a query is looked up
PAUSE = 350

HERE = os.path.dirname(os.path.abspath(__file__))
PY_WTK = lookup.PY_WTK


def icon() -> str:
    """py-wtk's icon if py-wtk-install.py installed it, else a
    dictionary."""
    for base in (os.environ.get('XDG_DATA_HOME') or
                 os.path.expanduser('~/.local/share'), '/usr/share'):
        if glob.glob(os.path.join(base, 'icons', 'hicolor', '*', 'apps',
                                  'py-wtk.*')):
            return 'py-wtk'
    return 'accessories-dictionary'


def strip_prefix(query: str, prefix: str = PREFIX) -> str | None:
    """The query without PREFIX and a space, or None if it is not for
    us."""
    start = prefix.lower() + ' '
    if query.lower().startswith(start):
        return query[len(start):]
    return None


#  What asks for the settings, after the prefix: wtk ?
ASK_SETTINGS = ('?', 'settings')


def asks_settings(text: str) -> bool:
    """Whether TEXT (the query without the prefix) asks for the
    settings."""
    return text.strip().lower() in ASK_SETTINGS


def display(m: lookup.Match, definitions: int) -> str:
    """What KRunner shows of M (styled text, so escaped): the word, its
    language and part of speech, the headword line and the first
    DEFINITIONS.  (KRunner shows the subtext only for the selected match,
    beside the text: there is no room in it for the definitions.)"""
    e = html.escape
    if m.kind != 'entry':
        return e(lookup.shorten(m.text, 200))
    lines = [f'<b>{e(m.word)}</b> · {e(m.language)} · {e(m.part)}']
    if m.headword and m.headword != m.word:
        lines.append(f'<i>{e(lookup.shorten(m.headword))}</i>')
    shown = m.definitions[:definitions]
    lines += [f'{i}. {e(lookup.shorten(d))}' for i, d in enumerate(shown, 1)]
    if len(m.definitions) > len(shown):
        lines.append(f'<i>(+{len(m.definitions) - len(shown)} more)</i>')
    return '<br>'.join(lines)


def copy_text(text: str) -> None:
    """Puts TEXT in the clipboard: through Klipper, or else wl-copy or
    xclip."""
    try:
        klipper = dbus.SessionBus().get_object('org.kde.klipper', '/klipper')
        klipper.setClipboardContents(text,
                                     dbus_interface='org.kde.klipper.klipper')
        return
    except dbus.DBusException:
        pass
    for command in (['wl-copy'], ['xclip', '-selection', 'clipboard']):
        if shutil.which(command[0]):
            subprocess.run(command, input=text.encode(), check=False)
            return


def properties(**values) -> dbus.Dictionary:
    return dbus.Dictionary({'category': CATEGORY, **values}, signature='sv')


class Runner(dbus.service.Object):

    def __init__(self, bus, words: lookup.Lookup, py_wtk: str):
        # (without a bus, as in the tests: not exported)
        super().__init__(*((bus, PATH) if bus is not None else ()))
        self.words = words
        self.py_wtk = py_wtk
        self.icon = icon()
        self.found: dict[str, lookup.Match] = {}    # (of the last answer)
        self.latest = 0                 # (the number of the last query)
        self.lock = threading.Lock()    # (one lookup at a time)

    @dbus.service.method(IFACE, out_signature='a(sss)')
    def Actions(self):
        return [('copy', 'Copy', 'edit-copy'),
                ('online', 'Open on Wiktionary', 'internet-web-browser'),
                ('settings', 'Settings', 'configure')]

    @dbus.service.method(IFACE, in_signature='s',
                         out_signature='a(sssida{sv})',
                         async_callbacks=('reply', 'error'))
    def Match(self, query, reply, error):
        self.latest += 1
        number = self.latest
        mine = runner_settings.load()
        text = strip_prefix(str(query), mine.prefix)
        if text is None or not text.strip():
            reply([])
            return
        if asks_settings(text):
            self.found = {}
            reply([('settings', 'py-wtk settings', 'configure', EXACT, 1.0,
                    properties(subtext='The prefix, the languages and the '
                               'number of results',
                               actions=dbus.Array([], signature='s')))])
            return
        try:
            at_hand = self.words.remembered(text)
        except Exception as e:          # (KRunner shows nothing, else)
            print(f'krunner-py-wtk: {text!r}: {e!r}', file=sys.stderr)
            at_hand = None
        if at_hand is not None:
            reply(self.answer(at_hand))
            return

        def look_up():
            try:
                with self.lock:
                    found = [] if number != self.latest else \
                        self.words.matches(text)
            except Exception as e:
                print(f'krunner-py-wtk: {text!r}: {e!r}', file=sys.stderr)
                found = []
            GLib.idle_add(finish, found)

        def finish(found):
            # (an old query gets nothing: KRunner has moved on)
            reply(self.answer(found) if number == self.latest else [])
            return False

        def start():
            if number != self.latest:   # (typing went on)
                reply([])
            else:
                threading.Thread(target=look_up, daemon=True).start()
            return False

        GLib.timeout_add(PAUSE, start)

    def answer(self, matches: list[lookup.Match]) -> list:
        """The matches as KRunner wants them; they are kept for Run."""
        definitions = self.words.mine.definitions
        self.found = {}
        out = []
        for i, m in enumerate(matches):
            key = str(i)
            self.found[key] = m
            kind = EXACT if m.kind == 'entry' else POSSIBLE
            out.append((key, display(m, definitions), self.icon, kind,
                        1.0 - i / 100, properties(multiline=True)))
        return out

    @dbus.service.method(IFACE, in_signature='ss')
    def Run(self, key, action):
        if str(key) == 'settings' or action == 'settings':
            self.open_settings()
            return
        m = self.found.get(str(key))
        if m is None:
            return
        if action == 'online':
            if m.url:
                webbrowser.open(m.url)
        elif action == 'copy':
            copy_text(m.full())
        else:
            self.open_window(m)

    def open_window(self, m: lookup.Match):
        """The window of py-wtk, with the word of M (in its language)."""
        args = [m.word]
        if m.kind == 'entry' and (m.code or m.language):
            args += ['-l', m.code or m.language]
        subprocess.Popen([sys.executable,
                          os.path.join(self.py_wtk, 'py-wtk-gui')] + args,
                         cwd=self.py_wtk, start_new_session=True)

    def open_settings(self):
        subprocess.Popen([sys.executable,
                          os.path.join(HERE, 'settings_dialog.py'),
                          '--py-wtk', self.py_wtk], start_new_session=True)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='py-wtk in KRunner (a D-Bus runner).')
    parser.add_argument('--py-wtk', default=PY_WTK, metavar='FOLDER',
                        help=f'the folder of py-wtk (default: {PY_WTK})')
    parser.add_argument('-V', '--version', action='version',
                        version=f'krunner-py-wtk {VERSION}')
    args = parser.parse_args(argv)
    lookup.use(args.py_wtk)
    words = lookup.Lookup()             # (before taking the name: loaded)
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    name = dbus.service.BusName(SERVICE, bus)  # noqa: F841 (kept)
    runner = Runner(bus, words, args.py_wtk)  # noqa: F841
    GLib.MainLoop().run()


if __name__ == '__main__':
    main()
