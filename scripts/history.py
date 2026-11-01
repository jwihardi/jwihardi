"""All-time authored stats from token-visible default branches, via GitHub GraphQL."""
import base64
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.request

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
        payload = json.dumps({'query':query, 'variables':variables}).encode()
        request = urllib.request.Request('https://api.github.com/graphql', data=payload,
            headers={'Authorization':'Bearer ' + self.token,
                     'Content-Type':'application/json', 'User-Agent':'profile-history'})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    result = json.load(response)
                if result.get('errors') or not result.get('data'):
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


def next_cursor(connection):
    info = connection['pageInfo']
    if not info['hasNextPage']:
        return None
    if not info['endCursor']:
        raise HistoryError('Missing pagination cursor')
    return info['endCursor']


def collect_history(query, user='jwihardi', cache=None):
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
        if cached and cached['head'] == head:
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
        fresh['repos'][repo_id] = {'head':head, 'commits':commits}
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
