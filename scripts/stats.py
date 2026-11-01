#!/usr/bin/env python3
"""Fetch owned public non-fork repository and star counts, across every page."""
import json
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
    # Finish all API requests before replacing the last successful snapshot.
    result = fetch_stats()
    path = ROOT / 'profile/stats.json'
    content = json.dumps(result, indent=2) + '\n'
    if not path.exists() or path.read_text() != content:
        temporary = path.with_suffix('.tmp')
        temporary.write_text(content)
        temporary.replace(path)


if __name__ == '__main__':
    main()
