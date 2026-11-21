"""Tests of the runner: the prefix, what KRunner is shown, and Match
called directly (not through D-Bus), with its pause and its thread."""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lookup  # noqa: E402
from test_lookup import FakeClient, Offline  # noqa: E402

try:
    import krunner_py_wk as k
    from gi.repository import GLib
except ImportError:
    k = None


@unittest.skipIf(k is None, 'needs python3-dbus and python3-gobject')
class PrefixTests(unittest.TestCase):

    def test_prefix(self):
        self.assertEqual(k.strip_prefix('wk rosa'), 'rosa')
        self.assertEqual(k.strip_prefix('Wk rosa'), 'rosa')
        self.assertIsNone(k.strip_prefix('firefox'))
        self.assertIsNone(k.strip_prefix('wtf'))
        self.assertIsNone(k.strip_prefix('w rosa'))
        self.assertIsNone(k.strip_prefix('wkx rosa'))
        self.assertEqual(k.strip_prefix('wi rosa', 'wi'), 'rosa')
        self.assertIsNone(k.strip_prefix('wk rosa', 'wi'))
        for text in ('?', ' settings', 'Settings '):
            self.assertTrue(k.asks_settings(text))
        self.assertFalse(k.asks_settings('rosa'))

    def test_display(self):
        m = lookup.Match('entry', 'rosa', 'Latin', 'la', 'Noun',
                         'rosa f <genitive>', ['rose', 'dear', 'love'])
        shown = k.display(m, 2)
        self.assertEqual(shown.split('<br>'), [
            '<b>rosa</b> · Latin · Noun', '<i>rosa f &lt;genitive&gt;</i>',
            '1. rose', '2. dear', '<i>(+1 more)</i>'])
        self.assertEqual(k.display(lookup.Match('note', 'x', text='a < b'), 3),
                         'a &lt; b')


@unittest.skipIf(k is None, 'needs python3-dbus and python3-gobject')
@unittest.skipUnless(lookup.is_py_wk(lookup.PY_WK), 'needs py-wk next to it')
class MatchTests(Offline):

    def setUp(self):
        super().setUp()
        self.runner = k.Runner(None, self.words, lookup.PY_WK)

    def ask(self, *queries):
        """Sends QUERIES one after another (as typing does), and returns
        their answers once all have come."""
        answers = {}
        loop = GLib.MainLoop()

        def replier(query):
            def reply(matches):
                answers[query] = matches
                if len(answers) == len(queries):
                    loop.quit()
            return reply
        for query in queries:
            self.runner.Match(query, replier(query), self.fail)
        if len(answers) < len(queries):     # (some are answered at once)
            GLib.timeout_add(5000, loop.quit)
            loop.run()
        return answers

    def test_match(self):
        answer = self.ask('wk rosa')['wk rosa']
        self.assertEqual(len(answer), 3)
        key, text, _, kind, relevance, props = answer[0]
        self.assertTrue(text.startswith('<b>rosa</b> · Latin · Noun'))
        self.assertEqual((kind, props['category'], props['multiline']),
                         (k.EXACT, 'py-wk', True))
        self.assertEqual(self.runner.found[key].part, 'Noun')

    def test_only_the_last_of_the_typing(self):
        answers = self.ask('wk r', 'wk ro', 'wk rosa')
        self.assertEqual((answers['wk r'], answers['wk ro']), ([], []))
        self.assertEqual(len(answers['wk rosa']), 3)
        self.assertEqual(FakeClient.asked, ['rosa'])     # (only it)

    def test_not_for_us(self):
        self.assertEqual(self.ask('firefox')['firefox'], [])
        self.assertEqual(self.ask('wk ')['wk '], [])
        answer = self.ask('wk ?')['wk ?']
        self.assertEqual(answer[0][0], 'settings')

    def test_suggestions(self):
        answer = self.ask('wk rosx')['wk rosx']
        self.assertEqual([a[3] for a in answer], [k.POSSIBLE, k.POSSIBLE])
        self.assertIn('rosaceous', answer[0][1])


if __name__ == '__main__':
    unittest.main()
