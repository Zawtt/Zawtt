from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


GRAPHQL_URL = "https://api.github.com/graphql"
SEARCH_URL = "https://api.github.com/search/issues"


def graphql(query: str, variables: dict[str, str], token: str) -> dict:
    request = Request(
        GRAPHQL_URL,
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Zawtt-profile-rhythm-activity",
        },
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError(json.dumps(payload["errors"], indent=2))
    return payload["data"]


def search_count(query: str, token: str) -> int:
    request = Request(
        f"{SEARCH_URL}?q={quote(query)}&per_page=1",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Zawtt-profile-rhythm-activity",
        },
    )
    with urlopen(request, timeout=30) as response:
        return int(json.load(response)["total_count"])


def activity_stats(login: str, token: str) -> dict:
    query = """
    query RhythmActivity($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """
    data = graphql(query, {"login": login}, token)
    user = data["user"]
    if user is None:
        raise RuntimeError(f"GitHub user not found: {login}")

    calendar = user["contributionsCollection"]["contributionCalendar"]
    days = [day for week in calendar["weeks"] for day in week["contributionDays"]]
    weeks = [sum(day["contributionCount"] for day in week["contributionDays"]) for week in calendar["weeks"]][-13:]
    weeks = [0] * (13 - len(weeks)) + weeks

    combo = 0
    max_combo = 0
    for day in sorted(days, key=lambda item: item["date"]):
        combo = combo + 1 if day["contributionCount"] > 0 else 0
        max_combo = max(max_combo, combo)

    misses = search_count(f"user:{login} is:issue is:open", token) + search_count(
        f"user:{login} is:pr is:open", token
    )
    notes = int(calendar["totalContributions"])
    accuracy = round(notes / (notes + misses) * 100) if notes + misses else 100
    rank = "S" if notes > 0 and accuracy >= 98 else "A" if accuracy >= 90 else "B" if accuracy >= 75 else "C" if accuracy >= 50 else "D"
    return {
        "weekly": weeks,
        "max_combo": max_combo,
        "accuracy": accuracy,
        "notes": notes,
        "misses": misses,
        "rank": rank,
    }


def graph_geometry(values: list[int]) -> tuple[str, list[tuple[float, float, bool]]]:
    left = 74.0
    right = 1018.0
    bottom = 248.0
    height = 92.0
    maximum = max(max(values), 1)
    step = (right - left) / (len(values) - 1)
    highlighted = {index for index in sorted(range(len(values)), key=lambda index: values[index], reverse=True)[:3] if values[index] > 0}
    points = [
        (left + index * step, bottom - value / maximum * height, index in highlighted)
        for index, value in enumerate(values)
    ]
    path = " ".join(("M" if index == 0 else "L") + f" {x:.1f} {y:.1f}" for index, (x, y, _) in enumerate(points))
    return path, points


def gif_data_uri(path: Path) -> str:
    payload = path.read_bytes()
    if not (payload.startswith(b"GIF87a") or payload.startswith(b"GIF89a")):
        raise RuntimeError(f"Rhythm background is not a GIF: {path}")
    return "data:image/gif;base64," + base64.b64encode(payload).decode("ascii")


def render(stats: dict, background_gif: str) -> str:
    path, points = graph_geometry(stats["weekly"])
    rank_color = {"S": "#79df70", "A": "#8fb0ff", "B": "#d4b96f", "C": "#db8b68", "D": "#d46b78"}[stats["rank"]]
    circles = []
    for index, (x, y, highlighted) in enumerate(points):
        color = "#87dd78" if highlighted else "#8ea7ff"
        radius = 8 if highlighted else 5
        circles.append(
            f'''<circle cx="{x:.1f}" cy="{y:.1f}" r="0" fill="{color}" filter="url(#pointGlow)">
      <animate attributeName="r" from="0" to="{radius}" begin="{0.18 + index * 0.07:.2f}s" dur="0.28s" fill="freeze"/>
    </circle>'''
        )
    circles_svg = "\n    ".join(circles)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 420" role="img" aria-labelledby="title description">
  <title id="title">GitHub contributions rhythm-game activity panel</title>
  <desc id="description">Now playing contributions.rhy with a weekly activity graph, rank, maximum combo, accuracy, notes hit, and misses.</desc>
  <defs>
    <linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#101326"/>
      <stop offset="1" stop-color="#0d1020"/>
    </linearGradient>
    <linearGradient id="line" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#52658f"/>
      <stop offset="0.48" stop-color="#7d8fd1"/>
      <stop offset="0.68" stop-color="#81d878"/>
      <stop offset="1" stop-color="#52658f"/>
    </linearGradient>
    <linearGradient id="scrim" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#090c19" stop-opacity="0.98"/>
      <stop offset="0.48" stop-color="#090c19" stop-opacity="0.94"/>
      <stop offset="0.72" stop-color="#090c19" stop-opacity="0.58"/>
      <stop offset="1" stop-color="#090c19" stop-opacity="0.32"/>
    </linearGradient>
    <linearGradient id="bottomScrim" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0.48" stop-color="#090c19" stop-opacity="0"/>
      <stop offset="1" stop-color="#090c19" stop-opacity="0.62"/>
    </linearGradient>
    <clipPath id="panelClip">
      <rect x="10" y="10" width="1100" height="400" rx="18"/>
    </clipPath>
    <filter id="pointGlow" x="-120%" y="-120%" width="340%" height="340%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>

  <style>
    .trace {{ stroke-dasharray: 1800; stroke-dashoffset: 1800; animation: draw 1.8s ease-out forwards; }}
    .rank {{ animation: pulse 2.7s ease-in-out infinite; transform-origin: center; }}
    .card {{ animation: rise .65s ease-out both; }}
    .card-b {{ animation-delay: .08s; }}
    .card-c {{ animation-delay: .16s; }}
    .card-d {{ animation-delay: .24s; }}
    @keyframes draw {{ to {{ stroke-dashoffset: 0 }} }}
    @keyframes pulse {{ 0%,100% {{ opacity: .82 }} 50% {{ opacity: 1 }} }}
    @keyframes rise {{ from {{ opacity: 0; transform: translateY(8px) }} to {{ opacity: 1; transform: translateY(0) }} }}
  </style>

  <rect x="10" y="10" width="1100" height="400" rx="18" fill="url(#panel)"/>
  <g clip-path="url(#panelClip)">
    <image href="{background_gif}" x="666" y="10" width="444" height="400" preserveAspectRatio="xMidYMid slice"/>
    <rect x="10" y="10" width="1100" height="400" fill="url(#scrim)"/>
    <rect x="10" y="10" width="1100" height="400" fill="url(#bottomScrim)"/>
  </g>
  <rect x="10.75" y="10.75" width="1098.5" height="398.5" rx="17.25" fill="none" stroke="#303851" stroke-opacity="0.72" stroke-width="1.5"/>

  <text x="48" y="54" fill="#7782aa" font-family="Segoe UI, Arial, sans-serif" font-size="14" letter-spacing="1">now playing</text>
  <text x="48" y="88" fill="#e8ebff" font-family="Segoe UI, Arial, sans-serif" font-size="25" font-weight="700">contributions.rhy</text>

  <text x="1042" y="52" text-anchor="end" fill="#7782aa" font-family="Segoe UI, Arial, sans-serif" font-size="13" letter-spacing="1">rank</text>
  <text x="1042" y="91" text-anchor="end" fill="{rank_color}" font-family="Segoe UI, Arial, sans-serif" font-size="38" font-weight="800" class="rank">{stats['rank']}</text>

  <path d="M48 248H1060" stroke="#29304d" stroke-width="1"/>
  <path d="{path}" fill="none" stroke="url(#line)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="trace"/>
  {circles_svg}
  <path d="M1060 134v126" stroke="#d6d9ed" stroke-width="2" stroke-opacity="0.72"/>

  <g class="card">
    <rect x="48" y="292" width="246" height="82" rx="10" fill="#14192e" fill-opacity="0.91" stroke="#414967" stroke-opacity="0.34"/>
    <text x="171" y="321" text-anchor="middle" fill="#7d87ad" font-family="Segoe UI, Arial, sans-serif" font-size="13">max combo</text>
    <text x="171" y="353" text-anchor="middle" fill="#f0f2ff" font-family="Segoe UI, Arial, sans-serif" font-size="23" font-weight="700">x{stats['max_combo']}</text>
  </g>
  <g class="card card-b">
    <rect x="306" y="292" width="246" height="82" rx="10" fill="#14192e" fill-opacity="0.91" stroke="#414967" stroke-opacity="0.34"/>
    <text x="429" y="321" text-anchor="middle" fill="#7d87ad" font-family="Segoe UI, Arial, sans-serif" font-size="13">accuracy</text>
    <text x="429" y="353" text-anchor="middle" fill="#f0f2ff" font-family="Segoe UI, Arial, sans-serif" font-size="23" font-weight="700">{stats['accuracy']}%</text>
  </g>
  <g class="card card-c">
    <rect x="564" y="292" width="246" height="82" rx="10" fill="#14192e" fill-opacity="0.91" stroke="#414967" stroke-opacity="0.34"/>
    <text x="687" y="321" text-anchor="middle" fill="#7d87ad" font-family="Segoe UI, Arial, sans-serif" font-size="13">notes hit</text>
    <text x="687" y="353" text-anchor="middle" fill="#f0f2ff" font-family="Segoe UI, Arial, sans-serif" font-size="23" font-weight="700">{stats['notes']}</text>
  </g>
  <g class="card card-d">
    <rect x="822" y="292" width="246" height="82" rx="10" fill="#14192e" fill-opacity="0.91" stroke="#414967" stroke-opacity="0.34"/>
    <text x="945" y="321" text-anchor="middle" fill="#7d87ad" font-family="Segoe UI, Arial, sans-serif" font-size="13">misses</text>
    <text x="945" y="353" text-anchor="middle" fill="#79df70" font-family="Segoe UI, Arial, sans-serif" font-size="23" font-weight="700">{stats['misses']}</text>
  </g>

  <circle cx="1078" cy="28" r="2.4" fill="#7c819b"/>
  <circle cx="1088" cy="28" r="2.4" fill="#7c819b"/>
  <circle cx="1098" cy="28" r="2.4" fill="#7c819b"/>
</svg>
'''


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required")

    login = os.environ.get("GITHUB_USER", "Zawtt")
    output = Path(os.environ.get("RHYTHM_OUTPUT", "dist/contributions-rhythm.svg"))
    background = Path(os.environ.get("RHYTHM_BACKGROUND", "assets/nokotan-anime.gif"))
    if not background.is_file():
        raise RuntimeError(f"Rhythm background GIF not found: {background}")
    stats = activity_stats(login, token)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(stats, gif_data_uri(background)), encoding="utf-8")
    print(f"Generated {output}: {stats}")


if __name__ == "__main__":
    main()
