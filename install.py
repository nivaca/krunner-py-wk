#!/usr/bin/env python3
"""Installs (or, with --uninstall, removes) the py-wk runner for the
current user:

    ~/.local/share/krunner/dbusplugins/py-wk.desktop       tells KRunner
    ~/.local/share/dbus-1/services/SERVICE.service          starts it
    ~/.local/share/applications/krunner-py-wk-settings.desktop
                                            the settings, in the menu

    python3 install.py [--py-wk FOLDER] [--uninstall]

(uninstall.py is the same as --uninstall.)  Both also remove the files of
the versions named krunner-py-wtk, and stop that runner.  Then KRunner is
restarted (it starts again when called).
"""

import argparse
import os
import signal
import subprocess
import sys

from krunner_py_wk import HERE, PATH, PREFIX, PY_WK, SERVICE, VERSION
from lookup import is_py_wk

DATA = os.environ.get('XDG_DATA_HOME') or \
    os.path.expanduser('~/.local/share')
PLUGIN = os.path.join(DATA, 'krunner', 'dbusplugins', 'py-wk.desktop')
STARTER = os.path.join(DATA, 'dbus-1', 'services', SERVICE + '.service')
MENU = os.path.join(DATA, 'applications', 'krunner-py-wk-settings.desktop')

#  Los archivos de las versiones llamadas krunner-py-wtk, que se quitan al
#  instalar y al desinstalar (solo si son de este programa; véase is_old)
OLD_SERVICE = 'io.github.nivaca.PyWtkKRunner'
OLD_FILES = (
    os.path.join(DATA, 'krunner', 'dbusplugins', 'py-wtk.desktop'),
    os.path.join(DATA, 'dbus-1', 'services', OLD_SERVICE + '.service'),
    os.path.join(DATA, 'applications', 'krunner-py-wtk-settings.desktop'),
)
OLD_PROGRAM = 'krunner_py_wtk.py'
#  What only those files have: the service, the runner or the folder
OLD_MARKS = (OLD_SERVICE, OLD_PROGRAM, os.sep + 'krunner-py-wtk' + os.sep)

DESKTOP = f"""[Desktop Entry]
Name=py-wk
Comment=The English Wiktionary: {PREFIX} WORD, or {PREFIX} WORD @la
Icon=accessories-dictionary
Type=Service
X-KDE-PluginInfo-Author=Nicolas Vaughan
X-KDE-PluginInfo-Name=py-wk
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


def command(program: str, py_wk: str) -> str:
    """The command line that runs PROGRAM (of this folder) with py-wk in
    PY_WK, for an Exec line."""
    return ' '.join(exec_arg(a) for a in (
        sys.executable, os.path.join(HERE, program), '--py-wk', py_wk))


def menu(py_wk: str) -> str:
    return ('[Desktop Entry]\nType=Application\n'
            'Name=py-wk in KRunner\n'
            'Comment=Settings of the py-wk runner\n'
            f'Exec={command("settings_dialog.py", py_wk)}\n'
            'Icon=accessories-dictionary\n'
            'Categories=Settings;Utility;\n')


def service(py_wk: str) -> str:
    return (f'[D-BUS Service]\nName={SERVICE}\n'
            f'Exec={command("krunner_py_wk.py", py_wk)}\n')


def is_old(path: str) -> bool:
    """Whether PATH is a file that krunner-py-wtk's install.py wrote (it
    names that runner's service, program or folder)."""
    if os.path.islink(path) or not os.path.isfile(path):
        return False
    try:
        with open(path, encoding='utf-8') as f:
            text = f.read()
    except (OSError, UnicodeDecodeError):
        return False
    return any(mark in text for mark in OLD_MARKS)


def stop_runner() -> None:
    """Stops the runner, if it is running: the Python processes whose
    program is krunner_py_wk.py (not an editor or a shell that only
    names it), and those of krunner-py-wtk (krunner_py_wtk.py, wherever
    it was)."""
    program = os.path.realpath(os.path.join(HERE, 'krunner_py_wk.py'))
    for pid in os.listdir('/proc'):
        if not pid.isdigit():
            continue
        try:
            with open(f'/proc/{pid}/cmdline', 'rb') as f:
                argv = f.read().split(b'\0')
        except OSError:
            continue
        if len(argv) < 2 or b'python' not in os.path.basename(argv[0]):
            continue
        script = argv[1].decode(errors='replace')
        if os.path.realpath(script) == program or \
                os.path.basename(script) == OLD_PROGRAM:
            try:
                os.kill(int(pid), signal.SIGTERM)
            except OSError:
                pass


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Install the py-wk runner for KRunner.')
    parser.add_argument('--py-wk', default=PY_WK, metavar='FOLDER',
                        help=f'the folder of py-wk (default: {PY_WK})')
    parser.add_argument('--uninstall', action='store_true',
                        help='remove the runner')
    args = parser.parse_args(argv)
    for path in OLD_FILES:
        if is_old(path):
            os.remove(path)
            print(f'Removed {path} (of krunner-py-wtk)')
    if args.uninstall:
        for path in (PLUGIN, STARTER, MENU):
            if os.path.exists(path):
                os.remove(path)
                print(f'Removed {path}')
    else:
        py_wk = os.path.abspath(os.path.expanduser(args.py_wk))
        if not is_py_wk(py_wk):
            sys.exit(f'install.py: py-wk is not in {py_wk} (see --py-wk)')
        for path, text in ((PLUGIN, DESKTOP), (STARTER, service(py_wk)),
                           (MENU, menu(py_wk))):
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
