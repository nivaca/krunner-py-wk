"""Tests of the settings of the runner (runner_settings.py)."""

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import runner_settings  # noqa: E402
from runner_settings import RunnerSettings  # noqa: E402


class SettingsTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = os.environ.get('XDG_CONFIG_HOME')
        os.environ['XDG_CONFIG_HOME'] = self.tmp.name

    def tearDown(self):
        if self.old is None:
            del os.environ['XDG_CONFIG_HOME']
        else:
            os.environ['XDG_CONFIG_HOME'] = self.old
        self.tmp.cleanup()

    def test_saved_and_read(self):
        self.assertEqual(runner_settings.load(), RunnerSettings())
        self.assertIsNone(runner_settings.stamp())
        mine = RunnerSettings('wi', 'la, Old English', 5, 2)
        runner_settings.save(mine)
        self.assertEqual(runner_settings.load(), mine)
        self.assertIsNotNone(runner_settings.stamp())

    def test_prefix(self):
        for wrong in ('', '  ', 'w t'):
            self.assertIsNone(runner_settings.good_prefix(wrong))
        self.assertEqual(runner_settings.good_prefix(' wk '), 'wk')
        os.makedirs(os.path.dirname(runner_settings.path()))
        with open(runner_settings.path(), 'w') as f:
            f.write('[runner]\nprefix = w t\n')
        self.assertEqual(runner_settings.load().prefix, 'wk')

    def test_wrong_values(self):
        os.makedirs(os.path.dirname(runner_settings.path()))
        for text, results, definitions in (
                ('results = many', 12, 3), ('results = 0', 1, 3),
                ('results = 999\ndefinitions = 99', 50, 10),
                ('definitions = -1', 12, 1)):
            with open(runner_settings.path(), 'w') as f:
                f.write(f'[runner]\n{text}\n')
            s = runner_settings.load()
            self.assertEqual((s.results, s.definitions),
                             (results, definitions), text)
        with open(runner_settings.path(), 'w') as f:
            f.write('not an ini file [')
        self.assertEqual(runner_settings.load(), RunnerSettings())


if __name__ == '__main__':
    unittest.main()
