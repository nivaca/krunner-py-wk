krunner-py-wtk
==============

Version 1.0.

[py-wtk](https://github.com/nivaca/py-wtk), the English Wiktionary, in
KRunner (KDE Plasma 6): type `wtk` and a word, and its entries appear.

    wtk rosa            the entries of "rosa", in the languages of py-wtk
    wtk rosa @la        only Latin (codes or names: @la,es  @Spanish)
    wtk ice cream @en   expressions of several words

Each match is the entry of one part of speech of one language: the word,
the language and the part of speech, then the headword line (`rosa f
(genitive rosae); first declension`) and the first definitions.  A word
without a page gives the pages whose titles begin like it ("did you
mean").

Enter opens the entry in the window of py-wtk, in its language; the
actions copy the entry (with all its definitions), open it on Wiktionary,
and open the settings of the runner.  The entries follow the settings of
py-wtk (the languages, the preferred languages first), as its window and
command line do.

Wiktionary is on the network, so the runner waits for a short pause in
the typing before it asks (the queries replaced by the next keystroke are
never sent), and asks on a thread, so KRunner is never kept waiting.  The
pages stay in py-wtk's disk cache, and the last results in memory: a word
looked up a moment ago is shown at once.

Settings
--------

In KRunner, `wtk ?` (or `wtk settings`) gives a single match, "py-wtk
settings", that opens a small window with the settings of the runner
itself.  So do "py-wtk in KRunner" in the application menu, the Settings
action of each match, and `python3 settings_dialog.py`:

- the prefix that starts a search (`wtk` as usual): a word, without
  spaces;
- the languages shown: as in py-wtk, or others for KRunner only (codes
  or names, separated by commas, or `all`); `@` in a query overrides them;
- how many results to show, at most (12 as usual);
- how many definitions each match shows (3 as usual; Copy takes them
  all).

They are kept in `~/.config/krunner-py-wtk/settings.ini`, and seen at the
next search.

Installing
----------

It needs py-wtk (by default in the folder `py-wtk`, or `py-wkt`, next to
this one), and the D-Bus bindings of Python, which Fedora KDE usually has
already:

    $ sudo dnf install python3-dbus python3-gobject

Then:

    $ python3 install.py [--py-wtk FOLDER]

This writes three files, and restarts KRunner:

- `~/.local/share/krunner/dbusplugins/py-wtk.desktop`: tells KRunner
  about the runner.  KRunner sends it every query; the runner answers only
  those that start with the prefix.
- `~/.local/share/dbus-1/services/io.github.nivaca.PyWtkKRunner.service`:
  lets D-Bus start `krunner_py_wtk.py` the first time KRunner needs it.
  It stays running, so each query is quick.
- `~/.local/share/applications/krunner-py-wtk-settings.desktop`: the
  settings, in the application menu.

If py-wtk's `py-wtk-install.py` installed its icon, the matches show it.

`python3 uninstall.py` (or `python3 install.py --uninstall`) removes
them, stops the runner and restarts KRunner; this folder and py-wtk are
left as they are.  After changing the program or moving py-wtk, run
`install.py` again (it also stops the running runner).  The runner can be
turned off in System Settings > Search > KRunner.

How it works
------------

- `krunner_py_wtk.py`: the D-Bus runner (the interface
  `org.kde.krunner1`: Actions, Match, Run).  Match answers asynchronously:
  at once when the results are at hand, else after the pause, from a
  thread.
- `lookup.py`: the matches for a query, from py-wtk (its client of
  Wiktionary, its rendering of entries in brief); it knows nothing of
  D-Bus.
- `settings_dialog.py`: the settings window; `runner_settings.py`: the
  file that keeps them.
- `install.py`: the three files above; `uninstall.py` removes them.
- `tests/`: `python3 -m unittest discover -s tests` (no network needed:
  they use a made-up page).

To see what it does, stop it (`python3 -c 'import install;
install.stop_runner()'`) and start it by hand, `python3
krunner_py_wtk.py`: its errors are written to the terminal.

Licence
-------

GNU General Public License, version 3 or later (see LICENCE.txt), as
py-wtk.  © 2026 Nicolas Vaughan.  The content of the entries comes from
Wiktionary and its authors, under the licence CC BY-SA 4.0.
