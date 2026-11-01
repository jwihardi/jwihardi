import json
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import render


class GeneratorTests(unittest.TestCase):
    def test_all_variants_are_valid(self):
        data = json.loads((render.ROOT / 'profile/content.json').read_text())
        for theme in data['themes']:
            for mobile in (False, True):
                svg = render.render(data, theme, mobile)
                ET.fromstring(svg)
                self.assertNotIn('public repos', svg)
                self.assertNotIn('EMNIST', svg)
                self.assertIn('Gentoo Linux / Windows', svg)

    def test_themes_share_content_and_layout(self):
        data = json.loads((render.ROOT / 'profile/content.json').read_text())
        ns = {'s': 'http://www.w3.org/2000/svg'}
        def elements(theme):
            tree = ET.fromstring(render.render(data, theme))
            return [(e.attrib, e.text) for e in tree.findall('.//s:text', ns)]
        self.assertEqual(elements('dark'), elements('light'))

    def test_history_stats_layout_has_space(self):
        data = json.loads((render.ROOT / 'profile/content.json').read_text())
        data['stats'] = {'repos':1,'stars':2,'commits':3,'additions':4,'deletions':5,
                         'history_as_of':'2000-01-01'}
        for mobile in (False, True):
            tree = ET.fromstring(render.render(data, 'dark', mobile, 'warp'))
            ns = {'s':'http://www.w3.org/2000/svg'}
            labels = {e.text:e for e in tree.findall('s:text', ns)}
            self.assertIn('. Commits:', labels)
            self.assertIn('. Lines +:', labels)
            self.assertIn('. Lines −:', labels)
            bottom = float(tree.attrib['height'])
            self.assertTrue(all(float(e.attrib['y']) < bottom for e in tree.findall('s:text', ns)))
