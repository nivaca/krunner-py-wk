"""py-wtk for KRunner: the entries of a word, as short matches.

This part knows nothing of D-Bus, so it can be tested on its own.  It uses
the program in the folder of py-wtk (see `use`), with its settings (those
of the configuration file that its window and command line share) and its
disk cache of pages.

    rosa            the entries of "rosa", in the languages of the settings
    rosa @la        only Latin (codes or names: @la,es  @Latin @"Old English")
    ice cream       expressions of several words

Each match is the entry of one part of speech of one language: its
headword line and its first definitions.  A word without a page gives the
pages whose titles begin like it ("did you mean").
"""

from __future__ import annotations

import os
import re
import shlex
import sys
from collections import OrderedDict
from dataclasses import dataclass, field

import runner_settings

_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _usual_folder() -> str:
    """py-wtk next to this folder (its clone may be called py-wkt)."""
    for name in ('py-wtk', 'py-wkt'):
        folder = os.path.join(_PARENT, name)
        if is_py_wtk(folder):
            return folder
    return os.path.join(_PARENT, 'py-wtk')


def is_py_wtk(folder: str) -> bool:
    return os.path.isfile(os.path.join(folder, 'pywtk', '__init__.py'))


#  py-wtk, if no other folder is given
PY_WTK = _usual_folder()
#  How many results of a query are remembered (the pages are on disk too)
REMEMBERED = 40
#  A definition is cut after so many characters (KRunner has little room)
SHORT = 110


@dataclass
class Match:
    """One result for KRunner.  KIND is 'entry' (WORD in LANGUAGE, as PART
    of speech), 'suggestion' (a page whose title begins like the word) or
    'note' (no entry, or no connection: TEXT says why)."""
    kind: str
    word: str
    language: str = ''
    code: str = ''
    part: str = ''
    headword: str = ''
    definitions: list[str] = field(default_factory=list)
    text: str = ''
    url: str = ''

    def full(self) -> str:
        """What is copied: the word, the headword and all the
        definitions."""
        if self.kind != 'entry':
            return self.text or self.word
        lines = [f'{self.word} ({self.language}, {self.part})']
        if self.headword:
            lines.append('  ' + self.headword)
        lines += [f'  {i}. {d}' for i, d in enumerate(self.definitions, 1)]
        return '\n'.join(lines)


def use(folder: str) -> None:
    """Makes the package of py-wtk in FOLDER importable."""
    folder = os.path.abspath(os.path.expanduser(folder))
    if not is_py_wtk(folder):
        raise FileNotFoundError(f'py-wtk is not in {folder}')
    if folder not in sys.path:
        sys.path.insert(0, folder)


def parse_query(text: str) -> tuple[str, str | None]:
    """(the word, the languages asked with @, or None): 'rosa @la @es' ->
    ('rosa', 'la,es').  The @ words may be anywhere, and quoted."""
    try:
        tokens = shlex.split(text)
    except ValueError:                  # (an open quote, while typing)
        tokens = text.split()
    words, languages = [], []
    for t in tokens:
        if t.startswith('@'):
            languages += [x for x in t[1:].split(',') if x.strip()]
        else:
            words.append(t)
    return ' '.join(words), (','.join(languages) or None)


def shorten(text: str, most: int = SHORT) -> str:
    if len(text) <= most:
        return text
    return text[:most - 1].rsplit(' ', 1)[0].rstrip(',;:') + '…'


_NUMBERED = re.compile(r'^(\s*)\d+\.\s+(.*)$')


def entries(rendered_lines: list[str], toc, word: str, language,
            parts_of_speech) -> list[Match]:
    """The entries (a Match for each part of speech) of LANGUAGE, from its
    rendering in brief: TOC holds (depth, title, line)."""
    from pywtk.api import page_url
    from pywtk.entry import norm_title
    lines = rendered_lines
    starts = [line for _, _, line in toc] + [len(lines)]
    out = []
    for i, (depth, title, line) in enumerate(toc):
        if depth == 0 or norm_title(title) not in parts_of_speech:
            continue
        end = next(s for s in starts[i + 1:] if s > line)
        body = [l for l in lines[line + 1:end] if l.strip()]
        headword = ''
        definitions: list[tuple[int, str]] = []
        for l in body:
            m = _NUMBERED.match(l)
            if m:
                definitions.append((len(m.group(1)), m.group(2).strip()))
            elif not headword and not definitions:
                headword = ' '.join(l.split())
        senses: list[str] = []          # (the senses, not their sub-senses,
        if definitions:                 # but those of "inflection of x:")
            top = min(indent for indent, _ in definitions)
            subs: list[str] = []
            for indent, d in definitions + [(top, '')]:
                if indent > top:
                    subs.append(d)
                    continue
                if senses and senses[-1].endswith(':') and subs:
                    senses[-1] += ' ' + '; '.join(subs)
                subs = []
                if d:
                    senses.append(d)
        out.append(Match(
            'entry', word, language.name, language.code, title, headword,
            senses,
            url=page_url(word) + '#' + language.name.replace(' ', '_')))
    return out


class Lookup:
    """The matches of queries.  `use` must be called first.  CLIENT makes
    the client of Wiktionary, and SUGGEST(word, limit) gives the titles that
    begin like a word (both from py-wtk, as usual; the tests give others)."""

    def __init__(self, client=None, suggest=None):
        from pywtk.api import suggestions
        self._client = client
        self._suggest = suggest or suggestions
        self._remembered: OrderedDict[tuple, list[Match]] = OrderedDict()
        self.mine = runner_settings.load()

    def settings(self):
        """py-wtk's settings and the runner's, read again (they are small
        files, and may have changed in the window of either)."""
        from pywtk.settings import Settings
        self.mine = runner_settings.load()
        return Settings()

    def _key(self, query: str, st) -> tuple | None:
        word, languages = parse_query(query)
        if not word:
            return None
        languages = languages or self.mine.languages or \
            st['general.languages']
        return (word, languages, tuple(st['general.preferred_languages']),
                self.mine.definitions)

    def remembered(self, query: str) -> list[Match] | None:
        """The matches of QUERY if they are at hand (no need to wait)."""
        key = self._key(query, self.settings())
        found = self._remembered.get(key) if key else None
        return None if found is None else found[:self.mine.results]

    def matches(self, query: str) -> list[Match]:
        """The matches of QUERY: the entries of the word, or suggestions if
        it has no page.  May take a while (it can ask Wiktionary)."""
        from pywtk.api import NetworkError, NotFound
        st = self.settings()
        key = self._key(query, st)
        if key is None:
            return []
        if key in self._remembered:
            self._remembered.move_to_end(key)
            return self._remembered[key][:self.mine.results]
        word, languages, preferred, _ = key
        # (a new client each time: its memory of pages would only grow;
        # the pages stay in the disk cache of py-wtk)
        client = self._client() if self._client else st.client()
        try:
            root = client.page(word)
        except NotFound:
            found = self._missing(word)
        except NetworkError as e:
            # (not remembered: the next query tries again)
            return [Match('note', word, text='Cannot reach Wiktionary: '
                          f'{getattr(e, "reason", e)}')]
        else:
            found = self._entries(word, root, languages, list(preferred))
        self._remembered[key] = found
        while len(self._remembered) > REMEMBERED:
            self._remembered.popitem(last=False)
        return found[:self.mine.results]

    def _missing(self, word: str) -> list[Match]:
        from pywtk.api import page_url
        titles = self._suggest(word, limit=self.mine.results)
        if not titles:
            return [Match('note', word, text=f'No Wiktionary entry for '
                          f'“{word}”', url=page_url(word))]
        return [Match('suggestion', t, text=f'Did you mean “{t}”?',
                      url=page_url(t)) for t in titles]

    def _entries(self, word, root, languages, preferred) -> list[Match]:
        from pywtk.api import page_url
        from pywtk.entry import (PARTS_OF_SPEECH, Options, available_languages,
                                 language_sections, select_languages)
        from pywtk.render import Style, render_entry
        langs = language_sections(root)
        chosen = select_languages(langs, languages, preferred)
        if not chosen:
            return [Match('note', word, text=f'No entry in {languages}; on '
                          f'the page: {available_languages(langs)}',
                          url=page_url(word))]
        options = Options.build(brief=True)
        out = []
        for lang in chosen:
            view = render_entry(word, [lang], Style(False), 100_000, options)
            found = entries(view.lines, view.toc, word, lang, PARTS_OF_SPEECH)
            out += found or [Match('entry', word, lang.name, lang.code,
                                   'Entry', url=page_url(word) + '#' +
                                   lang.name.replace(' ', '_'))]
        return out
