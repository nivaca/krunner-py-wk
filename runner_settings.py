"""The settings of the runner itself (those of the entries come from
py-wtk): ~/.config/krunner-py-wtk/settings.ini

    [runner]
    prefix = wtk        ; what starts a search in KRunner: wtk rosa
    languages = la, es  ; the languages shown (empty: as py-wtk says)
    results = 12        ; at most so many matches
    definitions = 3     ; the definitions shown in each match

(Not settings.py: py-wtk has a module of that name.)
"""

from __future__ import annotations

import configparser
import os
from dataclasses import dataclass

SECTION = 'runner'
PREFIX = 'wtk'                  # (as usual)
RESULTS = 12                    # (as usual)
MOST_RESULTS = 50
DEFINITIONS = 3                 # (as usual)
MOST_DEFINITIONS = 10


def path() -> str:
    base = os.environ.get('XDG_CONFIG_HOME') or \
        os.path.expanduser('~/.config')
    return os.path.join(base, 'krunner-py-wtk', 'settings.ini')


@dataclass
class RunnerSettings:
    prefix: str = PREFIX
    languages: str = ''         # ('': those of py-wtk)
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
