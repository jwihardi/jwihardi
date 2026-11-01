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
                self.assertIn('Gentoo Linux / OpenRC', svg)

    def test_themes_share_content_and_layout(self):
        data = json.loads((render.ROOT / 'profile/content.json').read_text())
        ns = {'s': 'http://www.w3.org/2000/svg'}
        def elements(theme):
            tree = ET.fromstring(render.render(data, theme))
            return [(e.attrib, e.text) for e in tree.findall('.//s:text', ns)]
        self.assertEqual(elements('dark'), elements('light'))
