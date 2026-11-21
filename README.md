krunner-py-wk
=============

Version 1.1.  (Up to 1.0.1 it was called krunner-py-wtk, with the prefix
`wtk`; see "Installing" to move to it.)

[py-wk](https://github.com/nivaca/py-wk), the English Wiktionary, in
KRunner (KDE Plasma 6): type `wk` and a word, and its entries appear.

    wk rosa            the entries of "rosa", in the languages of py-wk
    wk rosa @la        only Latin (codes or names: @la,es  @Spanish)
    wk ice cream @en   expressions of several words

Each match is the entry of one part of speech of one language: the word,
the language and the part of speech, then the headword line (`rosa f
(genitive rosae); first declension`) and the first definitions.  A word
without a page gives the pages whose titles begin like it ("did you
mean").

Enter opens the entry in the window of py-wk, in its language; the
actions copy the entry (with all its definitions), open it on Wiktionary,
and open the settings of the runner.  The entries follow the settings of
py-wk (the languages, the preferred languages first), as its window and
command line do.

Wiktionary is on the network, so the runner waits for a short pause in
the typing before it asks (the queries replaced by the next keystroke are
never sent), and asks on a thread, so KRunner is never kept waiting.  The
pages stay in py-wk's disk cache, and the last results in memory: a word
looked up a moment ago is shown at once.

Settings
--------

In KRunner, `wk ?` (or `wk settings`) gives a single match, "py-wk
settings", that opens a small window with the settings of the runner
itself.  So do "py-wk in KRunner" in the application menu, the Settings
action of each match, and `python3 settings_dialog.py`:

- the prefix that starts a search (`wk` as usual): a word, without
  spaces;
- the languages shown: as in py-wk, or others for KRunner only (codes
  or names, separated by commas, or `all`); `@` in a query overrides them;
- how many results to show, at most (12 as usual);
- how many definitions each match shows (3 as usual; Copy takes them
  all).

They are kept in `~/.config/krunner-py-wk/settings.ini`, and seen at the
next search.

Installing
----------

It needs Python 3.14 or later, py-wk (by default in the folder `py-wk`,
or `py-wtk` or `py-wkt`, its earlier names, next to this one), and the
D-Bus bindings of Python, which Fedora KDE usually has already:

    $ sudo dnf install python3-dbus python3-gobject

Then:

    $ python3 install.py [--py-wk FOLDER]

This writes three files, and restarts KRunner:

- `~/.local/share/krunner/dbusplugins/py-wk.desktop`: tells KRunner
  about the runner.  KRunner sends it every query; the runner answers only
  those that start with the prefix.
- `~/.local/share/dbus-1/services/io.github.nivaca.PyWkKRunner.service`:
  lets D-Bus start `krunner_py_wk.py` the first time KRunner needs it.
  It stays running, so each query is quick.
- `~/.local/share/applications/krunner-py-wk-settings.desktop`: the
  settings, in the application menu.

If py-wk's `py-wk-install.py` installed its icon, the matches show it.

`python3 uninstall.py` (or `python3 install.py --uninstall`) removes
them, stops the runner and restarts KRunner; this folder and py-wk are
left as they are.  After changing the program or moving py-wk, run
`install.py` again (it also stops the running runner).  The runner can be
turned off in System Settings > Search > KRunner.

Coming from krunner-py-wtk (1.0.1 or earlier): run `python3 install.py`
in this folder.  It removes the three files that krunner-py-wtk wrote,
stops that runner, and writes its own.  The settings in
`~/.config/krunner-py-wtk/settings.ini` move to
`~/.config/krunner-py-wk/` the first time the runner reads them; a prefix
you had chosen is kept, but if it was the usual `wtk` (left as it was, or
saved in the file), type `wk` now, or set the prefix again.

How it works
------------

- `krunner_py_wk.py`: the D-Bus runner (the interface
  `org.kde.krunner1`: Actions, Match, Run).  Match answers asynchronously:
  at once when the results are at hand, else after the pause, from a
  thread.
- `lookup.py`: the matches for a query, from py-wk (its client of
  Wiktionary, its rendering of entries in brief); it knows nothing of
  D-Bus.
- `settings_dialog.py`: the settings window; `runner_settings.py`: the
  file that keeps them.
- `install.py`: the three files above; `uninstall.py` removes them.
- `tests/`: `python3 -m unittest discover -s tests` (no network needed:
  they use a made-up page).

To see what it does, stop it (`python3 -c 'import install;
install.stop_runner()'`) and start it by hand, `python3
krunner_py_wk.py`: its errors are written to the terminal.

Licence
-------

GNU General Public License, version 3 or later (see LICENCE.txt), as
py-wk.  © 2026 Nicolas Vaughan.  The content of the entries comes from
Wiktionary and its authors, under the licence CC BY-SA 4.0.
