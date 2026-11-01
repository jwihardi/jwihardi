import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

spec = importlib.util.spec_from_file_location('render', Path(__file__).resolve().parents[1] / 'scripts/render.py')
render = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render)


class GeneratorTests(unittest.TestCase):
    def test_pagination_and_consistent_repository_set(self):
        def repo(i, owner='jwihardi', fork=False, private=False, stars=2):
            return dict(id=i, owner={'login': owner}, fork=fork, private=private, stargazers_count=stars)
        responses = iter([
            ({'followers': 19}, ''),
            ([repo(1), repo(2, fork=True), repo(3, private=True), repo(4, owner='other')], '<https://api.github.com/page2>; rel="next"'),
            ([repo(1), repo(5, stars=4)], '')])
        self.assertEqual(render.fetch_stats('jwihardi', lambda url: next(responses)), {'repos': 2, 'stars': 6, 'followers': 19})

    def test_failed_refresh_preserves_every_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'profile').mkdir()
            (root / 'profile/content.json').write_text('{"user":"jwihardi"}')
            for name in ['README.md', 'profile/stats.json', 'profile-dark.svg']:
                (root / name).write_text('last good content')
            before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
            with patch.object(render, 'ROOT', root), patch('sys.argv', ['render.py', '--fetch-stats']), patch.object(render, 'fetch_stats', side_effect=OSError('API unavailable')):
                with self.assertRaises(OSError):
                    render.main()
            self.assertEqual(before, {p: p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_all_variants_are_valid_and_stats_can_be_omitted(self):
        data = json.loads((render.ROOT / 'profile/content.json').read_text())
        for theme in data['themes']:
            for mobile in (False, True):
                svg = render.render(data, None, theme, mobile)
                ET.fromstring(svg)
                self.assertNotIn('public repos', svg)
                self.assertIn('Gentoo Linux / OpenRC', svg)

    def test_themes_share_content_and_layout(self):
        data = json.loads((render.ROOT / 'profile/content.json').read_text())
        ns = {'s': 'http://www.w3.org/2000/svg'}
        def elements(theme):
            tree = ET.fromstring(render.render(data, {'repos': 15, 'stars': 6, 'followers': 19}, theme))
            return [(e.attrib, e.text) for e in tree.findall('.//s:text', ns)]
        self.assertEqual(elements('dark'), elements('light'))


if __name__ == '__main__':
    unittest.main()
