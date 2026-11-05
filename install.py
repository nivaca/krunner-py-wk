#!/usr/bin/env python3
"""Installs (or, with --uninstall, removes) the py-wtk runner for the
current user:

    ~/.local/share/krunner/dbusplugins/py-wtk.desktop       tells KRunner
    ~/.local/share/dbus-1/services/SERVICE.service          starts it
    ~/.local/share/applications/krunner-py-wtk-settings.desktop
                                            the settings, in the menu

    python3 install.py [--py-wtk FOLDER] [--uninstall]

(uninstall.py is the same as --uninstall.)  Then KRunner is restarted
(it starts again when called).
"""

import argparse
import os
import signal
import subprocess
import sys

from krunner_py_wtk import HERE, PATH, PREFIX, PY_WTK, SERVICE, VERSION
from lookup import is_py_wtk

DATA = os.environ.get('XDG_DATA_HOME') or \
    os.path.expanduser('~/.local/share')
PLUGIN = os.path.join(DATA, 'krunner', 'dbusplugins', 'py-wtk.desktop')
STARTER = os.path.join(DATA, 'dbus-1', 'services', SERVICE + '.service')
MENU = os.path.join(DATA, 'applications', 'krunner-py-wtk-settings.desktop')

DESKTOP = f"""[Desktop Entry]
Name=py-wtk
Comment=The English Wiktionary: {PREFIX} WORD, or {PREFIX} WORD @la
Icon=accessories-dictionary
Type=Service
X-KDE-PluginInfo-Author=Nicolas Vaughan
X-KDE-PluginInfo-Name=py-wtk
X-KDE-PluginInfo-Version={VERSION}
X-KDE-PluginInfo-License=GPL-3.0-or-later
X-KDE-PluginInfo-EnabledByDefault=true
X-Plasma-API=DBus
X-Plasma-API-Minimum-Version=2.0
X-Plasma-DBusRunner-Service={SERVICE}
X-Plasma-DBusRunner-Path={PATH}
X-Plasma-Runner-Min-Letter-Count=3
"""


def exec_arg(arg: str) -> str:
    """ARG quoted for an Exec line, as the desktop entry specification asks
    (in double quotes, which D-Bus's .service files take as well)."""
    if arg and not any(c in arg for c in ' \t\n"\'\\><~|&;$*?#()`'):
        return arg
    for c in '\\"`$':
        arg = arg.replace(c, '\\' + c)
    return f'"{arg}"'


def command(program: str, py_wtk: str) -> str:
    """The command line that runs PROGRAM (of this folder) with py-wtk in
    PY_WTK, for an Exec line."""
    return ' '.join(exec_arg(a) for a in (
        sys.executable, os.path.join(HERE, program), '--py-wtk', py_wtk))


def menu(py_wtk: str) -> str:
    return ('[Desktop Entry]\nType=Application\n'
            'Name=py-wtk in KRunner\n'
            'Comment=Settings of the py-wtk runner\n'
            f'Exec={command("settings_dialog.py", py_wtk)}\n'
            'Icon=accessories-dictionary\n'
            'Categories=Settings;Utility;\n')


def service(py_wtk: str) -> str:
    return (f'[D-BUS Service]\nName={SERVICE}\n'
            f'Exec={command("krunner_py_wtk.py", py_wtk)}\n')


def stop_runner() -> None:
    """Stops the runner, if it is running: the Python processes whose
    program is krunner_py_wtk.py (not an editor or a shell that only
    names it)."""
    program = os.path.realpath(os.path.join(HERE, 'krunner_py_wtk.py'))
    for pid in os.listdir('/proc'):
        if not pid.isdigit():
            continue
        try:
            with open(f'/proc/{pid}/cmdline', 'rb') as f:
                argv = f.read().split(b'\0')
        except OSError:
            continue
        if len(argv) > 1 and b'python' in os.path.basename(argv[0]) and \
                os.path.realpath(argv[1].decode(errors='replace')) == program:
            try:
                os.kill(int(pid), signal.SIGTERM)
            except OSError:
                pass


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Install the py-wtk runner for KRunner.')
    parser.add_argument('--py-wtk', default=PY_WTK, metavar='FOLDER',
                        help=f'the folder of py-wtk (default: {PY_WTK})')
    parser.add_argument('--uninstall', action='store_true',
                        help='remove the runner')
    args = parser.parse_args(argv)
    if args.uninstall:
        for path in (PLUGIN, STARTER, MENU):
            if os.path.exists(path):
                os.remove(path)
                print(f'Removed {path}')
    else:
        py_wtk = os.path.abspath(os.path.expanduser(args.py_wtk))
        if not is_py_wtk(py_wtk):
            sys.exit(f'install.py: py-wtk is not in {py_wtk} (see --py-wtk)')
        for path, text in ((PLUGIN, DESKTOP), (STARTER, service(py_wtk)),
                           (MENU, menu(py_wtk))):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f'Wrote {path}')
    #  (D-Bus reads its .service files again: it does not watch a folder
    #  made after the session started)
    subprocess.run(['busctl', '--user', 'call', 'org.freedesktop.DBus',
                    '/org/freedesktop/DBus', 'org.freedesktop.DBus',
                    'ReloadConfig'], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    #  (the application menu sees the settings entry at once)
    subprocess.run(['kbuildsycoca6'], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    #  (a runner that is running keeps its old files)
    stop_runner()
    subprocess.run(['kquitapp6', 'krunner'], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print('KRunner restarted.')


if __name__ == '__main__':
    main()
