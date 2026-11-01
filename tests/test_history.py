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

    def test_rest_fallback_pages_and_filters_authors(self):
        from history import GitHub
        client = GitHub('test-only')
        lookup = {'repository':{'nameWithOwner':'owner/repo'}, 'author':{'login':'jwihardi'}}
        requests = []
        def get(url):
            requests.append(url)
            if 'sha=' in url:
                return [{'sha':'one','author':{'node_id':'author'}},
                        {'sha':'other','author':{'node_id':'another'}}], '<https://api.github.com/next>; rel="next"'
            if url.endswith('/next'):
                return [{'sha':'one','author':{'node_id':'author'}},
                        {'sha':'two','author':{'node_id':'author'}}], ''
            return {'stats':{'additions':8,'deletions':3}}, ''
        with patch.object(GitHub,'__call__',return_value=lookup), patch.object(client,'rest_get',side_effect=get):
            result = client.rest_history({'repo':'repo','head':'tip','author':'author'})
        nodes = result['node']['object']['history']['nodes']
        self.assertEqual([n['oid'] for n in nodes], ['one','two'])
        self.assertEqual(len(requests),4)

    def test_checkpoint_survives_later_failure(self):
        checkpoints = []
        def failing(q,v):
            if q == HISTORY and v['repo'] == 'b':
                raise HistoryError('transient')
            return self.query(q,v)
        with self.assertRaises(HistoryError):
            collect_history(failing, checkpoint=checkpoints.append)
        self.assertEqual(set(checkpoints[-1]['repos']), {'a'})
        result, _ = collect_history(self.query, cache=checkpoints[-1])
        self.assertEqual(result['commits'],2)

    def test_indexed_fallback_checks_ancestry(self):
        from history import GitHub
        client = GitHub('test-only')
        def get(url):
            if '/search/' in url:
                return {'total_count':2,'incomplete_results':False,'items':[
                    {'sha':'ancestor','author':{'node_id':'author'}},
                    {'sha':'side-branch','author':{'node_id':'author'}}]}, ''
            if '/compare/ancestor' in url:
                return {'status':'ahead'}, ''
            if '/compare/side-branch' in url:
                return {'status':'diverged'}, ''
            return {'stats':{'additions':8,'deletions':3}}, ''
        with patch.object(client,'rest_get',side_effect=get):
            result = client.search_history('https://api.github.com/repos/owner/repo','owner/repo','jwihardi',{'head':'tip','author':'author'})
        conn = result['node']['object']['history']
        self.assertEqual([n['oid'] for n in conn['nodes']], ['ancestor'])
        self.assertTrue(conn['indexed'])

    def test_indexed_fallback_refuses_partial_results(self):
        from history import GitHub
        client = GitHub('test-only')
        with patch.object(client,'rest_get',return_value=({'total_count':1,'incomplete_results':True,'items':[]},'')):
            with self.assertRaises(HistoryError):
                client.search_history('base','owner/repo','jwihardi',{'head':'tip','author':'author'})
