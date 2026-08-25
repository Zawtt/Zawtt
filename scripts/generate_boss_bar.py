from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape


SEARCH_URL = "https://api.github.com/search/issues"


def search_count(query: str, token: str) -> int:
    request = Request(
        f"{SEARCH_URL}?q={quote(query)}&per_page=1",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Zawtt-profile-boss-bar",
        },
    )
    with urlopen(request, timeout=30) as response:
        return int(json.load(response)["total_count"])


def backlog_stats(login: str, token: str) -> dict[str, int]:
    open_issues = search_count(f"user:{login} is:issue is:open", token)
    open_prs = search_count(f"user:{login} is:pr is:open", token)
    total_issues = search_count(f"user:{login} is:issue", token)
    total_prs = search_count(f"user:{login} is:pr", token)
    total = total_issues + total_prs
    open_total = open_issues + open_prs
    return {
        "open_issues": open_issues,
        "open_prs": open_prs,
        "open_total": open_total,
        "total": total,
        "resolved": max(0, total - open_total),
    }


def render(login: str, stats: dict[str, int]) -> str:
    open_total = stats["open_total"]
    total = stats["total"]
    hp_ratio = open_total / max(total, 1)
    hp_width = round(910 * hp_ratio)
    defeated = open_total == 0
    status = "DEFEATED — NO DAMAGE TAKEN" if defeated else f"BATTLE IN PROGRESS — {open_total} TARGETS REMAIN"
    status_color = "#8df0b7" if defeated else "#ff667d"
    status_glow = "#3ce58a" if defeated else "#ff334f"
    slash_opacity = "0" if defeated else "0.7"
    updated = datetime.now(timezone.utc).strftime("%Y.%m.%d")
    player = escape(login.upper())

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 330" role="img" aria-labelledby="title description">
  <title id="title">The Backlog boss HP bar</title>
  <desc id="description">Animated GitHub backlog boss. Open issues and pull requests are its remaining health.</desc>
  <defs>
    <linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#18121d" stop-opacity="0.98"/>
      <stop offset="0.55" stop-color="#100d16" stop-opacity="0.98"/>
      <stop offset="1" stop-color="#1c1018" stop-opacity="0.98"/>
    </linearGradient>
    <linearGradient id="frame" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#7f657f"/>
      <stop offset="0.35" stop-color="#d9b568"/>
      <stop offset="0.65" stop-color="#ff596f"/>
      <stop offset="1" stop-color="#7f657f"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="-0.3 0;0.3 0;-0.3 0" dur="8s" repeatCount="indefinite"/>
    </linearGradient>
    <linearGradient id="hp" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#8e1028"/>
      <stop offset="0.55" stop-color="#e32948"/>
      <stop offset="1" stop-color="#ff6b74"/>
    </linearGradient>
    <linearGradient id="slash" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="0.5" stop-color="#ffffff" stop-opacity="0.42"/>
      <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
    <pattern id="segments" width="52" height="38" patternUnits="userSpaceOnUse">
      <path d="M51 0v38" stroke="#f6d5d9" stroke-opacity="0.10"/>
    </pattern>
    <filter id="shadow" x="-20%" y="-40%" width="140%" height="190%">
      <feGaussianBlur in="SourceAlpha" stdDeviation="13" result="blur"/>
      <feFlood flood-color="#c43248" flood-opacity="0.24"/>
      <feComposite in2="blur" operator="in"/>
      <feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="glow" x="-100%" y="-100%" width="300%" height="300%">
      <feGaussianBlur stdDeviation="5" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>

  <style>
    .panel {{ animation: breathe 5.5s ease-in-out infinite; transform-origin: center; }}
    .status {{ animation: statusPulse 2.8s ease-in-out infinite; }}
    .ember-a {{ animation: ember 3s ease-in-out infinite; }}
    .ember-b {{ animation: ember 4s 1s ease-in-out infinite; }}
    .dash {{ animation: dash 10s linear infinite; }}
    @keyframes breathe {{ 0%, 100% {{ transform: translateY(0) }} 50% {{ transform: translateY(-2px) }} }}
    @keyframes statusPulse {{ 0%, 100% {{ opacity: .82 }} 50% {{ opacity: 1 }} }}
    @keyframes ember {{ 0%, 100% {{ opacity: .2; transform: translateY(0) }} 50% {{ opacity: .9; transform: translateY(-5px) }} }}
    @keyframes dash {{ to {{ stroke-dashoffset: -96 }} }}
  </style>

  <g class="panel" filter="url(#shadow)">
    <rect x="24" y="25" width="1072" height="280" rx="22" fill="url(#panel)" stroke="url(#frame)" stroke-width="2.5"/>
    <rect x="35" y="36" width="1050" height="258" rx="16" fill="none" stroke="#d2a970" stroke-opacity="0.18" stroke-dasharray="14 10" class="dash"/>

    <path d="M54 83V57h26M1040 57h26v26M54 246v26h26M1040 272h26v-26" fill="none" stroke="#d9b568" stroke-width="2.5" stroke-linecap="round"/>
    <path d="M46 104h1028M46 219h1028" stroke="#b98b65" stroke-opacity="0.17"/>

    <text x="58" y="77" fill="#b89aa4" font-family="Consolas, monospace" font-size="12" letter-spacing="3">WORLD BOSS // MAINTENANCE RAID</text>
    <text x="1060" y="77" text-anchor="end" fill="#806d7a" font-family="Consolas, monospace" font-size="10" letter-spacing="2">CHALLENGER {player}</text>

    <text x="560" y="116" text-anchor="middle" fill="#fff4ec" font-family="Segoe UI, Arial, sans-serif" font-size="29" font-weight="800" letter-spacing="7">THE BACKLOG</text>

    <rect x="105" y="137" width="910" height="38" rx="8" fill="#2a1820" stroke="#ab6f78" stroke-opacity="0.6"/>
    <rect x="105" y="137" width="{hp_width}" height="38" rx="8" fill="url(#hp)" filter="url(#glow)">
      <animate attributeName="width" from="0" to="{hp_width}" dur="1.45s" fill="freeze"/>
    </rect>
    <rect x="105" y="137" width="910" height="38" rx="8" fill="url(#segments)"/>
    <rect x="-170" y="138" width="150" height="36" fill="url(#slash)" opacity="{slash_opacity}">
      <animate attributeName="x" values="-170;1040" dur="4.8s" repeatCount="indefinite"/>
    </rect>
    <text x="560" y="163" text-anchor="middle" fill="#fff4f4" font-family="Consolas, monospace" font-size="17" font-weight="700" letter-spacing="2">HP {open_total:03d} / {total:03d}</text>

    <g class="status" filter="url(#glow)">
      <path d="M264 194h592" stroke="{status_glow}" stroke-opacity="0.28"/>
      <text x="560" y="211" text-anchor="middle" fill="{status_color}" font-family="Consolas, monospace" font-size="18" font-weight="700" letter-spacing="3">{escape(status)}</text>
    </g>

    <text x="84" y="254" fill="#8f7d89" font-family="Consolas, monospace" font-size="10" letter-spacing="2">OPEN ISSUES</text>
    <text x="191" y="255" fill="#f1e7e8" font-family="Consolas, monospace" font-size="15" font-weight="700">{stats['open_issues']:02d}</text>
    <text x="394" y="254" fill="#8f7d89" font-family="Consolas, monospace" font-size="10" letter-spacing="2">OPEN PULL REQUESTS</text>
    <text x="550" y="255" fill="#f1e7e8" font-family="Consolas, monospace" font-size="15" font-weight="700">{stats['open_prs']:02d}</text>
    <text x="768" y="254" fill="#8f7d89" font-family="Consolas, monospace" font-size="10" letter-spacing="2">RESOLVED</text>
    <text x="849" y="255" fill="#f1e7e8" font-family="Consolas, monospace" font-size="15" font-weight="700">{stats['resolved']:02d}</text>

    <circle cx="990" cy="111" r="3" fill="#ff5d74" class="ember-a"/>
    <circle cx="1023" cy="197" r="2" fill="#d9b568" class="ember-b"/>
    <circle cx="82" cy="193" r="2.5" fill="#ff5d74" class="ember-b"/>
    <path d="M1005 118l5 10 10 5-10 5-5 10-5-10-10-5 10-5z" fill="#d9b568" fill-opacity="0.7" class="ember-a"/>

    <text x="1056" y="284" text-anchor="end" fill="#665762" font-family="Consolas, monospace" font-size="9" letter-spacing="2">SYNC {updated}</text>
  </g>
</svg>
'''


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required")

    login = os.environ.get("GITHUB_USER", "Zawtt")
    output = Path(os.environ.get("BOSS_OUTPUT", "dist/boss-hp-bar.svg"))
    stats = backlog_stats(login, token)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(login, stats), encoding="utf-8")
    print(f"Generated {output}: {stats}")


if __name__ == "__main__":
    main()
