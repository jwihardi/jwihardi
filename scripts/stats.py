#!/usr/bin/env python3
"""Fetch owned public non-fork repository and star counts, across every page."""
import json
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def request_json(url):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'profile-stats',
               'X-GitHub-Api-Version': '2022-11-28'}
    if os.environ.get('GITHUB_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
        return json.load(response), response.headers.get('Link', '')


def fetch_stats(user='jwihardi', request=request_json):
    url = f'https://api.github.com/users/{user}/repos?type=owner&per_page=100'
    repositories = {}
    while url:
        page, links = request(url)
        if not isinstance(page, list):
            raise ValueError('Expected repository list')
        for repo in page:
            if not repo['fork'] and not repo['private'] and repo['owner']['login'].lower() == user.lower():
                stars = repo['stargazers_count']
                if type(stars) is not int or stars < 0:
                    raise ValueError('Invalid star count')
                repositories[repo['id']] = stars
        next_page = re.search(r'<([^>]+)>; rel="next"', links)
        url = next_page.group(1) if next_page else None
        if url and not url.startswith('https://api.github.com/'):
            raise ValueError('Unexpected pagination host')
    return {'repos': len(repositories), 'stars': sum(repositories.values())}


def main():
    # Fetch everything before replacing the last successful public snapshot.
    path = ROOT / 'profile/stats.json'
    previous = json.loads(path.read_text()) if path.exists() else {}
    result = fetch_stats()
    token = os.environ.get('ACCESS_TOKEN')
    if token:
        from history import GitHub, collect_history, load_cache, save_cache
        cache_path = ROOT / '.cache/history.enc'
        totals, cache = collect_history(GitHub(token), cache=load_cache(cache_path, token),
                                        checkpoint=lambda progress: save_cache(cache_path, token, progress))
        result.update(totals)
        result['history_as_of'] = datetime.now(timezone.utc).date().isoformat()
        save_cache(cache_path, token, cache)
    else:
        print('ACCESS_TOKEN is not configured; commit/line totals cannot be refreshed.')
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as summary:
                summary.write('History totals need an `ACCESS_TOKEN` repository secret. Public counts updated; existing history totals preserved.\n')
        # Keep the last successful totals, with their original observation date.
        for key in ('commits', 'additions', 'deletions', 'history_scope', 'history_as_of'):
            if key in previous:
                result[key] = previous[key]
    content = json.dumps(result, indent=2) + '\n'
    if not path.exists() or path.read_text() != content:
        temporary = path.with_suffix('.tmp')
        temporary.write_text(content)
        temporary.replace(path)


if __name__ == '__main__':
    main()
