import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from stats import fetch_stats


class StatsTests(unittest.TestCase):
    def test_pages_filtering_and_deduplication(self):
        def repo(i, fork=False, private=False, owner='jwihardi'):
            return {'id':i, 'fork':fork, 'private':private, 'owner':{'login':owner}, 'stargazers_count':3}
        pages = iter([
            ([repo(1),repo(2, fork=True),repo(3,private=True),repo(4,owner='other')], '<https://api.github.com/next>; rel="next"'),
            ([repo(1),repo(5)], '')])
        self.assertEqual(fetch_stats(request=lambda url: next(pages)), {'repos':2,'stars':6})

    def test_failure_does_not_return_partial_counts(self):
        def request(url):
            if 'next' in url:
                raise OSError('API unavailable')
            return [], '<https://api.github.com/next>; rel="next"'
        with self.assertRaises(OSError):
            fetch_stats(request=request)
