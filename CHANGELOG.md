# Changelog

All notable changes to krunner-py-wtk. The releases, with their zip
files, are on [GitHub](https://github.com/nivaca/krunner-py-wtk/releases);
the code is also on [Codeberg](https://codeberg.org/nivaca/krunner-py-wtk).

## 1.0.1 — 2026-11-17

- It requires Python 3.14 or later: the runner and the settings dialog
  stop with a message on an older Python. The README says so too.
- The zip `krunner-py-wtk-1.0.1.zip` has the whole program, to install
  with `python3 install.py [--py-wtk FOLDER]`. This is the first
  published release.

## 1.0 — 2026-11-05

- First version: py-wtk, the English Wiktionary, in KRunner (KDE Plasma
  6). After the prefix `wtk`, a word gives one match for each part of
  speech in each language, with the headword line and the first
  definitions; `@la` or `@Spanish` limits the languages, and a word
  without a page gives the pages whose titles begin like it.
- Enter opens the entry in the window of py-wtk. The actions copy the
  entry with all its definitions, open it on Wiktionary, and open the
  settings.
- Wiktionary is on the network, so the runner waits for a short pause in
  the typing and asks from a thread; the pages stay in py-wtk's disk
  cache, and the last results in memory.
- A settings window (`wtk ?`, the application menu, or
  `python3 settings_dialog.py`) for the prefix, the languages, the
  number of results and the number of definitions, kept in
  `~/.config/krunner-py-wtk/settings.ini`.
- `install.py` and `uninstall.py`, and tests that need no network.
- This version was not tagged or published as a release.
