"""All-time authored stats from token-visible default branches, via GitHub GraphQL."""
import base64
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.request
import urllib.parse
import re

IDENTITY = 'query { viewer { id login } }'
REPOSITORIES = '''query($login:String!, $cursor:String) {
  user(login:$login) {
    repositories(first:60, after:$cursor,
      ownerAffiliations:[OWNER,COLLABORATOR,ORGANIZATION_MEMBER]) {
      nodes { id defaultBranchRef { target { oid } } }
      pageInfo { hasNextPage endCursor }
    }
  }
}'''
HISTORY = '''query($repo:ID!, $head:GitObjectID!, $author:ID!, $cursor:String) {
  node(id:$repo) { ... on Repository {
    object(oid:$head) { ... on Commit {
      history(first:100, after:$cursor, author:{id:$author}) {
        nodes { oid additions deletions author { user { id } } }
        pageInfo { hasNextPage endCursor }
      }
    } }
  } }
}'''


class HistoryError(RuntimeError):
    pass


class GitHub:
    def __init__(self, token):
        self.token = token

    def __call__(self, query, variables):
        for attempt in range(3):
            # Reduce resolver work after a transient GraphQL failure.
            page_query = query.replace('history(first:100', 'history(first:25') if attempt else query
            payload = json.dumps({'query':page_query, 'variables':variables}).encode()
            request = urllib.request.Request('https://api.github.com/graphql', data=payload,
                headers={'Authorization':'Bearer ' + self.token,
                         'Content-Type':'application/json', 'User-Agent':'profile-history'})
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    result = json.load(response)
                if result.get('errors') or not result.get('data'):
                    messages = ' '.join(e.get('message', '').lower() for e in result.get('errors', []))
                    transient = any(part in messages for part in ('something went wrong', 'timed out', 'timeout'))
                    if transient and attempt < 2:
                        time.sleep(2 ** attempt)
                        continue
                    if transient and query == HISTORY:
                        return self.rest_history(variables)
                    # GraphQL errors may contain private repo names; do not log the payload.
                    raise HistoryError('GitHub rejected the history query; check token permissions and rate limits.')
                return result['data']
            except urllib.error.HTTPError as error:
                if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                    raise HistoryError(f'GitHub history request failed (HTTP {error.code}); previous totals preserved.') from None
                time.sleep(2 ** attempt)
            except (urllib.error.URLError, TimeoutError):
                if attempt == 2:
                    raise HistoryError('GitHub history request timed out; previous totals preserved.') from None
                time.sleep(2 ** attempt)
        raise HistoryError('History request failed')


    def rest_get(self, url):
        request = urllib.request.Request(url, headers={
            'Authorization':'Bearer ' + self.token,
            'Accept':'application/vnd.github+json', 'User-Agent':'profile-history',
            'X-GitHub-Api-Version':'2022-11-28'})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    return json.load(response), response.headers.get('Link', '')
            except urllib.error.HTTPError as error:
                if error.code not in (429,500,502,503,504) or attempt == 2:
                    raise HistoryError(f'History fallback failed (HTTP {error.code}); previous totals preserved.') from None
            except (urllib.error.URLError, TimeoutError):
                if attempt == 2:
                    raise HistoryError('History fallback timed out; previous totals preserved.') from None
            time.sleep(2 ** attempt)
        raise HistoryError('History fallback failed')

    def rest_history(self, variables):
        # Very large Git histories can time out in GraphQL's author filter.
        # REST uses the same pinned head and author, so the scope is unchanged.
        lookup = self('query($repo:ID!, $author:ID!){repository:node(id:$repo){...on Repository{nameWithOwner}} author:node(id:$author){...on User{login}}}',
                      {'repo':variables['repo'], 'author':variables['author']})
        repository = lookup['repository']['nameWithOwner']
        login = lookup['author']['login']
        base = 'https://api.github.com/repos/' + urllib.parse.quote(repository, safe='/')
        url = base + '/commits?' + urllib.parse.urlencode({'sha':variables['head'], 'author':login, 'per_page':100})
        commits = {}
        while url:
            try:
                page, links = self.rest_get(url)
            except HistoryError:
                return self.search_history(base, repository, login, variables)
            if not isinstance(page,list):
                raise HistoryError('Invalid fallback commit list')
            for commit in page:
                author = commit.get('author')
                if not author or author.get('node_id') != variables['author']:
                    continue
                oid = commit['sha']
                if oid in commits:
                    continue
                detail, _ = self.rest_get(base + '/commits/' + urllib.parse.quote(oid, safe=''))
                commits[oid] = {'oid':oid, 'additions':detail['stats']['additions'],
                                'deletions':detail['stats']['deletions'],
                                'author':{'user':{'id':variables['author']}}}
            following = re.search(r'<([^>]+)>; rel="next"', links)
            next_url = following.group(1) if following else None
            if next_url and (not next_url.startswith('https://api.github.com/') or next_url == url):
                raise HistoryError('Unexpected fallback pagination')
            url = next_url
        return {'node':{'object':{'history':{'nodes':list(commits.values()),
                'pageInfo':{'hasNextPage':False,'endCursor':None}}}}}


    def search_history(self, base, repository, login, variables):
        # GitHub's indexed endpoint avoids walking million-commit fork histories.
        # Refuse truncated/incomplete results; validate every match against the pinned head.
        url = 'https://api.github.com/search/commits?' + urllib.parse.urlencode({
            'q':f'repo:{repository} author:{login}', 'per_page':100})
        commits = {}
        seen = set()
        expected = None
        while url:
            result, links = self.rest_get(url)
            if result['incomplete_results'] or result['total_count'] > 1000:
                raise HistoryError('Indexed history is incomplete; previous totals preserved.')
            if expected is None:
                expected = result['total_count']
            elif expected != result['total_count']:
                raise HistoryError('History index changed during scan; retry later.')
            for commit in result['items']:
                oid = commit['sha']
                if oid in seen:
                    continue
                seen.add(oid)
                author = commit.get('author')
                if not author or author.get('node_id') != variables['author']:
                    continue
                if oid != variables['head']:
                    comparison, _ = self.rest_get(base + '/compare/' + oid + '...' + variables['head'] + '?per_page=1')
                    if comparison['status'] not in ('ahead','identical'):
                        continue
                detail, _ = self.rest_get(base + '/commits/' + oid)
                commits[oid] = {'oid':oid, 'additions':detail['stats']['additions'],
                                'deletions':detail['stats']['deletions'],
                                'author':{'user':{'id':variables['author']}}}
            following = re.search(r'<([^>]+)>; rel="next"', links)
            next_url = following.group(1) if following else None
            if next_url and (not next_url.startswith('https://api.github.com/') or next_url == url):
                raise HistoryError('Unexpected search pagination')
            url = next_url
        if len(seen) != expected:
            raise HistoryError('Incomplete indexed commit pages; previous totals preserved.')
        return {'node':{'object':{'history':{'nodes':list(commits.values()),
                'pageInfo':{'hasNextPage':False,'endCursor':None}, 'indexed':True}}}}


def next_cursor(connection):
    info = connection['pageInfo']
    if not info['hasNextPage']:
        return None
    if not info['endCursor']:
        raise HistoryError('Missing pagination cursor')
    return info['endCursor']


def collect_history(query, user='jwihardi', cache=None, checkpoint=None):
    """Publish nothing until every repository and commit page has succeeded."""
    identity = query(IDENTITY, {})['viewer']
    if identity['login'].lower() != user.lower():
        raise HistoryError('ACCESS_TOKEN must belong to the profile account.')
    previous = cache if cache and cache.get('author') == identity['id'] else {}
    previous_repos = previous.get('repos', {})
    repositories = {}
    cursor = None
    while True:
        connection = query(REPOSITORIES, {'login':user, 'cursor':cursor})['user']['repositories']
        for repo in connection['nodes']:
            if repo['defaultBranchRef']:
                repositories[repo['id']] = repo['defaultBranchRef']['target']['oid']
        following = next_cursor(connection)
        if following is None:
            break
        if following == cursor:
            raise HistoryError('Repository pagination did not advance')
        cursor = following
    fresh = {'version':1, 'author':identity['id'], 'repos':{}}
    unique = {}
    for repo_id, head in repositories.items():
        cached = previous_repos.get(repo_id)
        indexed = False
        if cached and cached['head'] == head and not cached.get('indexed'):
            commits = cached['commits']
        else:
            commits = {}
            cursor = None
            while True:
                response = query(HISTORY, {'repo':repo_id, 'head':head,
                                          'author':identity['id'], 'cursor':cursor})
                node = response.get('node')
                if not node or not node.get('object'):
                    raise HistoryError('Repository history became unavailable; previous totals preserved.')
                connection = node['object']['history']
                indexed = indexed or connection.get('indexed', False)
                for commit in connection['nodes']:
                    author = commit['author']['user']
                    if author and author['id'] == identity['id']:
                        values = [commit['additions'], commit['deletions']]
                        if any(type(n) is not int or n < 0 for n in values):
                            raise HistoryError('Invalid line-change counts')
                        commits[commit['oid']] = values
                following = next_cursor(connection)
                if following is None:
                    break
                if following == cursor:
                    raise HistoryError('Commit pagination did not advance')
                cursor = following
        fresh['repos'][repo_id] = {'head':head, 'commits':commits, 'indexed':indexed}
        if checkpoint:
            checkpoint({'version':1, 'author':identity['id'],
                        'repos':{**previous_repos, **fresh['repos']}})
        for oid, values in commits.items():
            if oid in unique and unique[oid] != values:
                raise HistoryError('Inconsistent counts for the same commit')
            unique[oid] = values
    totals = {'commits':len(unique), 'additions':sum(v[0] for v in unique.values()),
              'deletions':sum(v[1] for v in unique.values()),
              'history_scope':'accessible default-branch history'}
    return totals, fresh


def cipher(token):
    # The token is never stored. Rotating it also invalidates the encrypted cache.
    from cryptography.fernet import Fernet
    key = hashlib.sha256(('profile-history-cache-v1:' + token).encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def load_cache(path, token):
    if not path.exists():
        return None
    from cryptography.fernet import InvalidToken
    try:
        data = json.loads(cipher(token).decrypt(path.read_bytes()))
        return data if data.get('version') == 1 else None
    except (InvalidToken, ValueError):
        return None


def save_cache(path, token, cache):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_bytes(cipher(token).encrypt(json.dumps(cache).encode()))
    temporary.replace(path)
