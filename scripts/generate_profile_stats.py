import json
import os
import re
import urllib.request
from datetime import datetime
from html import unescape
from pathlib import Path

USERNAME = "akh112003"
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)


def get(url, accept="application/vnd.github+json"):
    req = urllib.request.Request(url, headers={
        "User-Agent": "akh112003-profile-stats",
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
    })
    token = os.getenv("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8")


def esc(value):
    return (str(value).replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def fetch_stats():
    user = json.loads(get(f"https://api.github.com/users/{USERNAME}"))
    repos = json.loads(get(f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=owner"))
    public_repos = sum(1 for r in repos if not r.get("fork"))
    stars = sum(r.get("stargazers_count", 0) for r in repos)
    forks = sum(r.get("forks_count", 0) for r in repos)
    return {
        "repos": public_repos,
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "stars": stars,
        "forks": forks,
    }


def stats_svg(stats):
    items = [
        ("Repositories", stats["repos"]),
        ("Followers", stats["followers"]),
        ("Stars", stats["stars"]),
        ("Forks", stats["forks"]),
    ]
    cards = []
    for i, (label, value) in enumerate(items):
        x = 25 + (i % 2) * 335
        y = 25 + (i // 2) * 88
        cards.append(f'''<rect x="{x}" y="{y}" width="305" height="68" rx="12" fill="#161b22" stroke="#30363d"/>
<text x="{x+20}" y="{y+28}" fill="#8b949e" font-size="14" font-family="Arial, sans-serif">{esc(label)}</text>
<text x="{x+20}" y="{y+54}" fill="#c084fc" font-size="23" font-weight="700" font-family="Arial, sans-serif">{esc(value)}</text>''')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="700" height="220" viewBox="0 0 700 220">
<rect width="700" height="220" rx="14" fill="#0d1117"/>
<text x="25" y="18" fill="#f0f6fc" font-size="12" font-family="Arial, sans-serif">akh112003 · public GitHub stats</text>
{''.join(cards)}
</svg>'''


def contribution_svg():
    html = get(f"https://github.com/users/{USERNAME}/contributions", accept="text/html")
    matches = re.findall(r'<td[^>]*data-date="([0-9-]+)"[^>]*data-level="([0-4])"[^>]*[^>]*>', html)
    if not matches:
        matches = re.findall(r'data-date="([0-9-]+)"[^>]*data-level="([0-4])"', html)
    cells = []
    for date, level in matches:
        cells.append((date, int(level)))
    cells.sort()
    # GitHub returns the calendar in chronological order. Group every 7 days into columns.
    colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    squares = []
    for i, (date, level) in enumerate(cells[-371:]):
        col = i // 7
        row = i % 7
        x = 18 + col * 14
        y = 48 + row * 14
        squares.append(f'<rect x="{x}" y="{y}" width="10" height="10" rx="2" fill="{colors[level]}"><title>{esc(date)} · level {level}</title></rect>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="170" viewBox="0 0 900 170">
<rect width="900" height="170" rx="14" fill="#0d1117"/>
<text x="18" y="24" fill="#f0f6fc" font-size="14" font-weight="700" font-family="Arial, sans-serif">GitHub Contribution Graph</text>
<text x="18" y="39" fill="#8b949e" font-size="11" font-family="Arial, sans-serif">Last year · generated from GitHub's public contribution calendar</text>
{''.join(squares)}
<text x="18" y="155" fill="#8b949e" font-size="10" font-family="Arial, sans-serif">Less</text>
{''.join(f'<rect x="{48+i*14}" y="147" width="10" height="10" rx="2" fill="{c}"/>' for i,c in enumerate(colors))}
<text x="120" y="155" fill="#8b949e" font-size="10" font-family="Arial, sans-serif">More</text>
</svg>'''


stats = fetch_stats()
(ASSETS / "github-stats.svg").write_text(stats_svg(stats), encoding="utf-8")
(ASSETS / "contribution-graph.svg").write_text(contribution_svg(), encoding="utf-8")
print("Generated profile stats and contribution graph.")
