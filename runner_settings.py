"""The settings of the runner itself (those of the entries come from
py-wk): ~/.config/krunner-py-wk/settings.ini

    [runner]
    prefix = wk        ; what starts a search in KRunner: wk rosa
    languages = la, es  ; the languages shown (empty: as py-wk says)
    results = 12        ; at most so many matches
    definitions = 3     ; the definitions shown in each match

(Not settings.py: py-wk has a module of that name.)  The settings of the
versions named krunner-py-wtk (~/.config/krunner-py-wtk/settings.ini) are
moved here once, when there are none yet.
"""

from __future__ import annotations

import configparser
import os
from dataclasses import dataclass

SECTION = 'runner'
PREFIX = 'wk'                  # (as usual)
RESULTS = 12                    # (as usual)
MOST_RESULTS = 50
DEFINITIONS = 3                 # (as usual)
MOST_DEFINITIONS = 10


def path(name: str = 'krunner-py-wk') -> str:
    base = os.environ.get('XDG_CONFIG_HOME') or \
        os.path.expanduser('~/.config')
    return os.path.join(base, name, 'settings.ini')


#  La carpeta de las versiones llamadas krunner-py-wtk
OLD_NAME = 'krunner-py-wtk'


def move_old() -> None:
    """The settings of krunner-py-wtk, moved here if there are none yet
    (its folder is removed if that leaves it empty)."""
    old = path(OLD_NAME)
    if os.path.exists(path()) or not os.path.isfile(old):
        return
    try:
        os.makedirs(os.path.dirname(path()), exist_ok=True)
        os.replace(old, path())
        os.rmdir(os.path.dirname(old))
    except OSError:
        pass                    # (si no se puede, quedan los habituales)


@dataclass
class RunnerSettings:
    prefix: str = PREFIX
    languages: str = ''         # ('': those of py-wk)
    results: int = RESULTS
    definitions: int = DEFINITIONS


def good_prefix(text: str) -> str | None:
    """TEXT as a prefix (a word, without spaces), or None if it cannot
    be one."""
    text = text.strip()
    if not text or any(c.isspace() for c in text):
        return None
    return text


def _number(text, usual: int, most: int) -> int:
    try:
        return min(max(int(text), 1), most)
    except (TypeError, ValueError):
        return usual


def load() -> RunnerSettings:
    """The saved settings (the usual ones where the file has nothing, or
    something wrong)."""
    move_old()
    parser = configparser.ConfigParser()
    try:
        parser.read(path(), encoding='utf-8')
    except configparser.Error:
        return RunnerSettings()
    section = parser[SECTION] if parser.has_section(SECTION) else {}
    return RunnerSettings(
        prefix=good_prefix(section.get('prefix', PREFIX)) or PREFIX,
        languages=section.get('languages', '').strip(),
        results=_number(section.get('results'), RESULTS, MOST_RESULTS),
        definitions=_number(section.get('definitions'), DEFINITIONS,
                            MOST_DEFINITIONS))


def save(s: RunnerSettings) -> None:
    parser = configparser.ConfigParser()
    parser[SECTION] = {'prefix': s.prefix, 'languages': s.languages,
                       'results': str(s.results),
                       'definitions': str(s.definitions)}
    os.makedirs(os.path.dirname(path()), exist_ok=True)
    tmp = path() + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        parser.write(f)
    os.replace(tmp, path())


def stamp() -> float | None:
    """When the file was last saved (None: there is none)."""
    try:
        return os.path.getmtime(path())
    except OSError:
        return None
