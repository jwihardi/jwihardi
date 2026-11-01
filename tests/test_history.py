import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from history import collect_history, HistoryError, IDENTITY, REPOSITORIES, HISTORY, save_cache, load_cache
import stats


def connection(nodes, cursor=None):
    return {'nodes':nodes, 'pageInfo':{'hasNextPage':cursor is not None, 'endCursor':cursor}}


def repo(name, head):
    return {'id':name, 'defaultBranchRef':{'target':{'oid':head}} if head else None}


def commit(oid, additions, deletions, author='author'):
    return {'oid':oid, 'additions':additions, 'deletions':deletions,
            'author':{'user':{'id':author} if author else None}}


class HistoryTests(unittest.TestCase):
    def query(self, query, variables):
        if query == IDENTITY:
            return {'viewer':{'id':'author','login':'jwihardi'}}
        if query == REPOSITORIES:
            nodes = [repo('a','tip-a'),repo('empty',None)] if variables['cursor'] is None else [repo('b','tip-b')]
            return {'user':{'repositories':connection(nodes, 'next' if variables['cursor'] is None else None)}}
        if variables['repo'] == 'a':
            nodes = [commit('shared',5,2),commit('unmapped',9,9,None)] if variables['cursor'] is None else [commit('only-a',7,3)]
            conn = connection(nodes, 'next' if variables['cursor'] is None else None)
        else:
            conn = connection([commit('shared',5,2),commit('other',100,100,'another')])
        return {'node':{'object':{'history':conn}}}

    def test_pagination_attribution_and_cross_repo_dedup(self):
        result, cache = collect_history(self.query)
        self.assertEqual((result['commits'],result['additions'],result['deletions']), (2,12,5))
        self.assertEqual(set(cache['repos']), {'a','b'})

    def test_unchanged_tips_use_cache(self):
        result, cache = collect_history(self.query)
        def query(q, v):
            self.assertNotEqual(q, HISTORY)
            return self.query(q,v)
        self.assertEqual(collect_history(query, cache=cache)[0], result)

    def test_rewritten_tip_replaces_old_counts(self):
        _, cache = collect_history(self.query)
        def query(q,v):
            if q == REPOSITORIES:
                return {'user':{'repositories':connection([repo('a','new-tip')])}}
            if q == HISTORY:
                return {'node':{'object':{'history':connection([commit('new',1,4)])}}}
            return self.query(q,v)
        result, updated = collect_history(query, cache=cache)
        self.assertEqual((result['commits'],result['additions'],result['deletions']), (1,1,4))
        self.assertNotIn('b', updated['repos'])

    def test_api_failure_preserves_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'profile').mkdir()
            file = root/'profile/stats.json'
            file.write_text('{"repos":15,"stars":6,"commits":42}')
            before = file.read_bytes()
            with patch.object(stats,'ROOT',root), patch.object(stats,'fetch_stats',return_value={'repos':16,'stars':7}), patch.dict('os.environ',{'ACCESS_TOKEN':'test-only'}), patch('history.collect_history',side_effect=HistoryError('failed')):
                with self.assertRaises(HistoryError): stats.main()
            self.assertEqual(file.read_bytes(),before)

    def test_cache_encrypted_and_token_rotation_invalidates(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory)/'cache.enc'
            value = {'version':1,'author':'private-identity','repos':{}}
            save_cache(file,'test-token',value)
            self.assertNotIn(b'private-identity',file.read_bytes())
            self.assertEqual(load_cache(file,'test-token'),value)
            self.assertIsNone(load_cache(file,'different-token'))
