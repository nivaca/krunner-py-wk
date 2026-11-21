"""Tests of the matches (lookup.py), with py-wk next to this folder and a
made-up page instead of Wiktionary (they need no network)."""

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import lookup  # noqa: E402
import runner_settings  # noqa: E402

#  A page as Wiktionary's REST API gives it, much shortened
PAGE = """<html><body>
<section><h2 id="Latin">Latin</h2>
 <section><h3>Etymology</h3><p>From <a href="./rhodon">rhodon</a>.</p></section>
 <section><h3>Noun</h3>
  <p><span class="headword-line"><strong class="Latn headword" lang="la">rosa</strong> f (genitive <a href="./rosae#Latin">rosae</a>); first declension</span></p>
  <ol><li><a href="./rose">rose</a> (flower)</li>
      <li>dear, sweetheart
        <dl><dd><i>mea rosa</i> ― my rose</dd></dl></li>
      <li>a third sense</li>
      <li>a fourth sense</li></ol>
  <section><h4>Declension</h4><table><tr><td>rosa</td><td>rosae</td></tr></table></section>
 </section>
 <section><h3>Participle</h3>
  <p><strong class="Latn headword" lang="la">rōsa</strong></p>
  <ol><li>inflection of rōsus:<ol><li>nominative feminine singular</li>
      <li>neuter plural</li></ol></li></ol>
 </section>
</section>
<section><h2 id="Spanish">Spanish</h2>
 <section><h3>Noun</h3>
  <p><strong class="Latn headword" lang="es">rosa</strong> f (plural rosas)</p>
  <ol><li>rose</li></ol>
 </section>
</section>
</body></html>"""


class FakeClient:
    """Wiktionary with one page, rosa; it counts the pages asked."""
    asked = []

    def page(self, title):
        from pywk.api import NotFound
        from pywk.dom import parse_html
        FakeClient.asked.append(title)
        if title != 'rosa':
            raise NotFound(title)
        return parse_html(PAGE)


class Offline(unittest.TestCase):
    """With empty settings (of py-wk and of the runner) and no network."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = os.environ.get('XDG_CONFIG_HOME')
        os.environ['XDG_CONFIG_HOME'] = self.tmp.name
        lookup.use(lookup.PY_WK)
        FakeClient.asked = []
        self.suggested = []

        def suggest(word, limit):
            self.suggested.append(word)
            return ['rosaceous', 'rosary'][:limit] if word == 'rosx' else []
        self.words = lookup.Lookup(client=FakeClient, suggest=suggest)

    def tearDown(self):
        if self.old is None:
            del os.environ['XDG_CONFIG_HOME']
        else:
            os.environ['XDG_CONFIG_HOME'] = self.old
        self.tmp.cleanup()


@unittest.skipUnless(lookup.is_py_wk(lookup.PY_WK), 'needs py-wk next to it')
class MatchTests(Offline):

    def test_entries(self):
        found = self.words.matches('rosa')
        self.assertEqual([(m.language, m.code, m.part) for m in found],
                         [('Latin', 'la', 'Noun'), ('Latin', 'la', 'Participle'),
                          ('Spanish', 'es', 'Noun')])
        noun = found[0]
        self.assertEqual(noun.headword,
                         'rosa f (genitive rosae); first declension')
        self.assertEqual(noun.definitions, ['rose (flower)', 'dear, sweetheart',
                                            'a third sense', 'a fourth sense'])
        self.assertEqual(noun.url, 'https://en.wiktionary.org/wiki/rosa#Latin')
        self.assertEqual(noun.full().splitlines()[:3], [
            'rosa (Latin, Noun)', '  rosa f (genitive rosae); first declension',
            '  1. rose (flower)'])

    def test_sub_senses(self):
        participle = self.words.matches('rosa @la')[1]
        self.assertEqual(participle.definitions, [
            'inflection of rōsus: nominative feminine singular; neuter plural'])

    def test_languages(self):
        for query in ('rosa @es', 'rosa @Spanish', '@es rosa', 'rosa @"Spanish"'):
            self.assertEqual([m.language for m in self.words.matches(query)],
                             ['Spanish'], query)
        self.assertEqual(len(self.words.matches('rosa @la,es')), 3)
        note = self.words.matches('rosa @de')
        self.assertEqual(note[0].kind, 'note')
        self.assertIn('Latin (la), Spanish (es)', note[0].text)

    def test_settings_of_the_runner(self):
        runner_settings.save(runner_settings.RunnerSettings(
            languages='es', results=5))
        self.assertEqual([m.language for m in self.words.matches('rosa')],
                         ['Spanish'])
        runner_settings.save(runner_settings.RunnerSettings(results=1))
        self.assertEqual(len(self.words.matches('rosa')), 1)

    def test_remembered(self):
        self.assertIsNone(self.words.remembered('rosa'))
        self.words.matches('rosa')
        self.assertEqual(len(self.words.remembered('rosa')), 3)
        self.words.matches('rosa')
        self.assertEqual(FakeClient.asked, ['rosa'])    # (asked once)

    def test_missing(self):
        found = self.words.matches('rosx')
        self.assertEqual([(m.kind, m.word) for m in found],
                         [('suggestion', 'rosaceous'), ('suggestion', 'rosary')])
        found = self.words.matches('qqqq')
        self.assertEqual(found[0].kind, 'note')
        self.assertIn('No Wiktionary entry', found[0].text)

    def test_network_errors_are_not_remembered(self):
        class Down:
            def page(self, title):
                raise OSError('no network')
        words = lookup.Lookup(client=Down)
        self.assertIn('Cannot reach', words.matches('rosa')[0].text)
        self.assertIsNone(words.remembered('rosa'))

    def test_empty(self):
        self.assertEqual(self.words.matches('  '), [])
        self.assertEqual(self.words.matches('@la'), [])


class QueryTests(unittest.TestCase):

    def test_parse_query(self):
        self.assertEqual(lookup.parse_query('rosa'), ('rosa', None))
        self.assertEqual(lookup.parse_query('ice cream @en'),
                         ('ice cream', 'en'))
        self.assertEqual(lookup.parse_query('rosa @la @es'), ('rosa', 'la,es'))
        self.assertEqual(lookup.parse_query('rosa @"Old English"'),
                         ('rosa', 'Old English'))
        self.assertEqual(lookup.parse_query('rock \'n'),
                         ('rock \'n', None))      # (an open quote)

    def test_shorten(self):
        self.assertEqual(lookup.shorten('short'), 'short')
        long = 'word ' * 40
        self.assertTrue(lookup.shorten(long).endswith('…'))
        self.assertLessEqual(len(lookup.shorten(long)), lookup.SHORT)


if __name__ == '__main__':
    unittest.main()
