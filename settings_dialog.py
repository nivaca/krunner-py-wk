#!/usr/bin/env python3
"""The settings of the py-wtk runner, in a small window:

    python3 settings_dialog.py [--py-wtk FOLDER]

The prefix of a search (wtk rosa), the languages shown (those of py-wtk,
or others for KRunner only), how many results to show and how many
definitions in each.  They are saved in runner_settings.path(); the runner
sees them at the next query.  The window has the look of py-wtk (its dark
mode, its fonts).
"""

import argparse
import sys
import tkinter as tk
from tkinter import messagebox, ttk

import lookup
import runner_settings
from runner_settings import (MOST_DEFINITIONS, MOST_RESULTS, RunnerSettings,
                             good_prefix)

if sys.version_info < (3, 14):
    sys.exit('krunner-py-wtk needs Python 3.14 or later.')


class Dialog:

    def __init__(self, root: tk.Tk):
        from pywtk.settings import Settings
        self.root = root
        usual = Settings()
        saved = runner_settings.load()
        self._look(usual)

        root.title('Settings of py-wtk in KRunner')
        frame = ttk.Frame(root, padding=16)
        frame.pack(fill='both', expand=True)
        frame.columnconfigure(1, weight=1)

        def label(row, text):
            ttk.Label(frame, text=text).grid(row=row, column=0, sticky='w',
                                             padx=(0, 12), pady=4)
        label(0, 'Prefix')
        self.prefix = tk.StringVar(value=saved.prefix)
        ttk.Entry(frame, textvariable=self.prefix, width=8).grid(
            row=0, column=1, sticky='w', pady=4)
        label(1, 'Languages')
        self.languages = tk.StringVar(value=saved.languages)
        ttk.Entry(frame, textvariable=self.languages, width=30).grid(
            row=1, column=1, sticky='we', pady=4)
        ttk.Label(frame, style='Muted.TLabel', justify='left', text=(
            'Codes or names, separated by commas (la, es, Old English), or '
            'all.\nEmpty: as in py-wtk ('
            f'{usual["general.languages"]}).')).grid(
                row=2, column=1, sticky='w', pady=(0, 6))
        label(3, 'Results, at most')
        self.results = tk.IntVar(value=saved.results)
        ttk.Spinbox(frame, from_=1, to=MOST_RESULTS, width=5,
                    textvariable=self.results).grid(row=3, column=1,
                                                    sticky='w', pady=4)
        label(4, 'Definitions in each')
        self.definitions = tk.IntVar(value=saved.definitions)
        ttk.Spinbox(frame, from_=1, to=MOST_DEFINITIONS, width=5,
                    textvariable=self.definitions).grid(row=4, column=1,
                                                        sticky='w', pady=4)
        self.note = ttk.Label(frame, style='Muted.TLabel', justify='left')
        self.note.grid(row=5, column=0, columnspan=2, sticky='w',
                       pady=(12, 0))
        self.prefix.trace_add('write', lambda *_: self._show_note())
        self._show_note()
        buttons = ttk.Frame(frame, padding=(0, 16, 0, 0))
        buttons.grid(row=6, column=0, columnspan=2, sticky='we')
        save = ttk.Button(buttons, text='Save', command=self.save)
        save.pack(side='right')
        ttk.Button(buttons, text='Cancel',
                   command=root.destroy).pack(side='right', padx=(0, 6))
        root.bind('<Return>', lambda e: self.save())
        root.bind('<Escape>', lambda e: root.destroy())
        save.focus_set()
        root.resizable(False, False)
        self._to_front()

    def _to_front(self):
        """Brings the window to the front: started from the runner (in
        the background), KWin would put it behind the others."""
        root = self.root
        root.lift()
        root.attributes('-topmost', True)
        root.after(300, lambda: root.attributes('-topmost', False))
        root.after(50, root.focus_force)

    def _show_note(self):
        """How to search, with the prefix being typed."""
        prefix = good_prefix(self.prefix.get())
        if prefix is None:
            text = 'The prefix is a word, without spaces.'
        else:
            text = (f'In KRunner, type: {prefix} WORD, or {prefix} WORD @la '
                    'for some languages only.\n'
                    'Changes are seen at the next search.')
        self.note.config(text=text)

    def _look(self, settings):
        """The dark mode and fonts of py-wtk, if they can be had."""
        try:
            from pywtk.gui_fonts import Fonts
            from pywtk.gui_theme import Theme
            Fonts.of(self.root, settings)
            Theme.of(self.root)
        except Exception:
            pass

    def chosen(self) -> RunnerSettings:
        def number(var, usual, most):
            try:
                return min(max(int(var.get()), 1), most)
            except (tk.TclError, ValueError):
                return usual
        return RunnerSettings(
            prefix=good_prefix(self.prefix.get()) or runner_settings.PREFIX,
            languages=' '.join(self.languages.get().split()),
            results=number(self.results, runner_settings.RESULTS,
                           MOST_RESULTS),
            definitions=number(self.definitions, runner_settings.DEFINITIONS,
                               MOST_DEFINITIONS))

    def save(self):
        if good_prefix(self.prefix.get()) is None:
            messagebox.showerror(parent=self.root, message=(
                'The prefix is a word, without spaces.'))
            return
        try:
            runner_settings.save(self.chosen())
        except OSError as e:
            messagebox.showerror(parent=self.root, message=(
                f'Cannot save the settings: {e.strerror}'))
            return
        self.root.destroy()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='The settings of py-wtk in KRunner.')
    parser.add_argument('--py-wtk', default=lookup.PY_WTK, metavar='FOLDER',
                        help=f'the folder of py-wtk (default: {lookup.PY_WTK})')
    args = parser.parse_args(argv)
    try:
        lookup.use(args.py_wtk)
    except FileNotFoundError as e:
        sys.exit(f'settings_dialog.py: {e}')
    root = tk.Tk(className='krunner-py-wtk')
    Dialog(root)
    root.mainloop()


if __name__ == '__main__':
    main()
