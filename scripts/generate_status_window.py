from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape


GRAPHQL_URL = "https://api.github.com/graphql"


def github_stats(login: str, token: str) -> dict[str, int]:
    query = """
    query ProfileStatus($login: String!) {
      user(login: $login) {
        contributionsCollection {
          totalCommitContributions
        }
        repositories(
          first: 100
          ownerAffiliations: OWNER
          privacy: PUBLIC
          orderBy: {field: UPDATED_AT, direction: DESC}
        ) {
          totalCount
          nodes {
            stargazerCount
            languages(first: 20, orderBy: {field: SIZE, direction: DESC}) {
              nodes { name }
            }
          }
        }
      }
    }
    """
    request = Request(
        GRAPHQL_URL,
        data=json.dumps({"query": query, "variables": {"login": login}}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Zawtt-profile-status-window",
        },
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)

    if payload.get("errors"):
        raise RuntimeError(json.dumps(payload["errors"], indent=2))

    user = payload["data"]["user"]
    if user is None:
        raise RuntimeError(f"GitHub user not found: {login}")

    repositories = user["repositories"]
    languages = {
        language["name"]
        for repository in repositories["nodes"]
        for language in repository["languages"]["nodes"]
    }
    return {
        "commits": user["contributionsCollection"]["totalCommitContributions"],
        "languages": len(languages),
        "stars": sum(repository["stargazerCount"] for repository in repositories["nodes"]),
        "repositories": repositories["totalCount"],
    }


def progress(value: int, target: int) -> int:
    if value <= 0:
        return 0
    return max(7, min(100, round(value / target * 100)))


def avatar_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def render(login: str, stats: dict[str, int], avatar: str) -> str:
    str_width = round(418 * progress(stats["commits"], 100) / 100)
    int_width = round(418 * progress(stats["languages"], 12) / 100)
    luk_width = round(418 * progress(stats["stars"], 25) / 100)
    updated = datetime.now(timezone.utc).strftime("%Y.%m.%d")
    player = escape(login.upper())

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 480" role="img" aria-labelledby="title description">
  <title id="title">{player}'s RPG-style GitHub status window</title>
  <desc id="description">Animated status window showing commits as strength, languages as intelligence, and stars as luck.</desc>
  <defs>
    <linearGradient id="glass" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#14294f" stop-opacity="0.96"/>
      <stop offset="0.52" stop-color="#101c39" stop-opacity="0.94"/>
      <stop offset="1" stop-color="#172a4b" stop-opacity="0.96"/>
    </linearGradient>
    <linearGradient id="frame" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#7ccfff"/>
      <stop offset="0.45" stop-color="#b8e8ff"/>
      <stop offset="0.7" stop-color="#9d8cff"/>
      <stop offset="1" stop-color="#6bbcf2"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="-0.3 0;0.3 0;-0.3 0" dur="7s" repeatCount="indefinite"/>
    </linearGradient>
    <linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#aeeaff" stop-opacity="0"/>
      <stop offset="0.5" stop-color="#aeeaff" stop-opacity="0.22"/>
      <stop offset="1" stop-color="#aeeaff" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#77c8ff"/>
      <stop offset="0.65" stop-color="#9b9bff"/>
      <stop offset="1" stop-color="#b9f0ff"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-30%" width="140%" height="170%">
      <feGaussianBlur in="SourceAlpha" stdDeviation="14" result="blur"/>
      <feFlood flood-color="#4a9ee8" flood-opacity="0.32"/>
      <feComposite in2="blur" operator="in"/>
      <feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="softGlow" x="-100%" y="-100%" width="300%" height="300%">
      <feGaussianBlur stdDeviation="4" result="glow"/>
      <feMerge><feMergeNode in="glow"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <clipPath id="avatarClip">
      <rect x="78" y="137" width="122" height="122" rx="18"/>
    </clipPath>
  </defs>

  <style>
    .window {{ animation: hover 5s ease-in-out infinite; transform-origin: center; }}
    .spark-a {{ animation: sparkle 2.8s ease-in-out infinite; }}
    .spark-b {{ animation: sparkle 3.4s 0.7s ease-in-out infinite; }}
    .dash {{ animation: dash 9s linear infinite; }}
    @keyframes hover {{ 0%, 100% {{ transform: translateY(0) }} 50% {{ transform: translateY(-3px) }} }}
    @keyframes sparkle {{ 0%, 100% {{ opacity: .25 }} 50% {{ opacity: 1 }} }}
    @keyframes dash {{ to {{ stroke-dashoffset: -80 }} }}
  </style>

  <g class="window" filter="url(#shadow)">
    <rect x="24" y="26" width="1072" height="426" rx="28" fill="url(#glass)" stroke="url(#frame)" stroke-width="2.5"/>
    <rect x="35" y="37" width="1050" height="404" rx="22" fill="none" stroke="#9bdcff" stroke-opacity="0.22" stroke-dasharray="12 10" class="dash"/>

    <path d="M52 88V61h27M1041 61h27v27M52 391v27h27M1041 418h27v-27" fill="none" stroke="#b5e9ff" stroke-width="3" stroke-linecap="round"/>
    <path d="M385 111v282" stroke="#91cbe9" stroke-opacity="0.22"/>
    <path d="M52 105h1016" stroke="#91cbe9" stroke-opacity="0.25"/>

    <text x="61" y="78" fill="#dff6ff" font-family="Segoe UI, Arial, sans-serif" font-size="25" font-weight="700" letter-spacing="7">STATUS WINDOW</text>
    <circle cx="922" cy="70" r="5" fill="#86d67c" filter="url(#softGlow)" class="spark-a"/>
    <text x="939" y="76" fill="#9ecce3" font-family="Consolas, monospace" font-size="13" letter-spacing="2">SYSTEM ONLINE</text>

    <rect x="58" y="124" width="303" height="277" rx="20" fill="#0b1530" fill-opacity="0.58" stroke="#8bd7ff" stroke-opacity="0.26"/>
    <rect x="71" y="130" width="136" height="136" rx="23" fill="#203961" stroke="#a6e4ff" stroke-opacity="0.65"/>
    <image href="{avatar}" x="78" y="137" width="122" height="122" preserveAspectRatio="xMidYMid slice" clip-path="url(#avatarClip)"/>

    <text x="226" y="150" fill="#86b9d5" font-family="Consolas, monospace" font-size="12" letter-spacing="2">PLAYER</text>
    <text x="226" y="181" fill="#f0fbff" font-family="Segoe UI, Arial, sans-serif" font-size="27" font-weight="700">{player}</text>
    <text x="226" y="211" fill="#9cafff" font-family="Consolas, monospace" font-size="14">LV. {stats['repositories']:02d}</text>
    <text x="226" y="239" fill="#86d67c" font-family="Consolas, monospace" font-size="12">ACTIVE</text>

    <text x="78" y="299" fill="#82b4cf" font-family="Consolas, monospace" font-size="11" letter-spacing="2">CLASS</text>
    <text x="78" y="326" fill="#e9f8ff" font-family="Segoe UI, Arial, sans-serif" font-size="20" font-weight="600">Roulette Operator</text>
    <text x="78" y="357" fill="#82b4cf" font-family="Consolas, monospace" font-size="11" letter-spacing="2">TITLE</text>
    <text x="78" y="384" fill="#e9f8ff" font-family="Segoe UI, Arial, sans-serif" font-size="20" font-weight="600">Professional Pretender</text>

    <text x="422" y="142" fill="#8dbed8" font-family="Consolas, monospace" font-size="12" letter-spacing="3">ATTRIBUTES</text>

    <text x="422" y="187" fill="#b6eaff" font-family="Consolas, monospace" font-size="23" font-weight="700">STR</text>
    <text x="500" y="187" fill="#ffffff" font-family="Consolas, monospace" font-size="25" font-weight="700">{stats['commits']:03d}</text>
    <text x="570" y="185" fill="#8fb8cd" font-family="Consolas, monospace" font-size="12" letter-spacing="1">COMMITS · LAST 12 MONTHS</text>
    <rect x="422" y="202" width="418" height="8" rx="4" fill="#253858"/>
    <rect x="422" y="202" width="{str_width}" height="8" rx="4" fill="url(#bar)" filter="url(#softGlow)">
      <animate attributeName="width" from="0" to="{str_width}" dur="1.25s" fill="freeze"/>
    </rect>

    <text x="422" y="270" fill="#b6eaff" font-family="Consolas, monospace" font-size="23" font-weight="700">INT</text>
    <text x="500" y="270" fill="#ffffff" font-family="Consolas, monospace" font-size="25" font-weight="700">{stats['languages']:03d}</text>
    <text x="570" y="268" fill="#8fb8cd" font-family="Consolas, monospace" font-size="12" letter-spacing="1">LANGUAGES DISCOVERED</text>
    <rect x="422" y="285" width="418" height="8" rx="4" fill="#253858"/>
    <rect x="422" y="285" width="{int_width}" height="8" rx="4" fill="url(#bar)" filter="url(#softGlow)">
      <animate attributeName="width" from="0" to="{int_width}" dur="1.45s" fill="freeze"/>
    </rect>

    <text x="422" y="353" fill="#b6eaff" font-family="Consolas, monospace" font-size="23" font-weight="700">LUK</text>
    <text x="500" y="353" fill="#ffffff" font-family="Consolas, monospace" font-size="25" font-weight="700">{stats['stars']:03d}</text>
    <text x="570" y="351" fill="#8fb8cd" font-family="Consolas, monospace" font-size="12" letter-spacing="1">STARS RECEIVED</text>
    <rect x="422" y="368" width="418" height="8" rx="4" fill="#253858"/>
    <rect x="422" y="368" width="{luk_width}" height="8" rx="4" fill="url(#bar)" filter="url(#softGlow)">
      <animate attributeName="width" from="0" to="{luk_width}" dur="1.65s" fill="freeze"/>
    </rect>

    <circle cx="1017" cy="143" r="3" fill="#b6ecff" class="spark-a"/>
    <circle cx="1042" cy="168" r="2" fill="#9d8cff" class="spark-b"/>
    <circle cx="994" cy="394" r="2.5" fill="#86d67c" class="spark-a"/>
    <path d="M1000 214l6 13 13 6-13 6-6 13-6-13-13-6 13-6z" fill="#a9e9ff" fill-opacity="0.7" class="spark-b"/>

    <rect x="43" y="90" width="1034" height="32" fill="url(#scan)" opacity="0.6">
      <animate attributeName="y" values="90;390;90" dur="9s" repeatCount="indefinite"/>
    </rect>
    <text x="1054" y="425" text-anchor="end" fill="#6f9ab2" font-family="Consolas, monospace" font-size="10" letter-spacing="2">SYNC {updated}</text>
  </g>
</svg>
'''


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required")

    login = os.environ.get("GITHUB_USER", "Zawtt")
    output = Path(os.environ.get("STATUS_OUTPUT", "dist/status-window.svg"))
    avatar_path = Path(os.environ.get("STATUS_AVATAR", "assets/profile-anime.jpg"))
    stats = github_stats(login, token)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(login, stats, avatar_data_uri(avatar_path)), encoding="utf-8")
    print(f"Generated {output}: {stats}")


if __name__ == "__main__":
    main()
