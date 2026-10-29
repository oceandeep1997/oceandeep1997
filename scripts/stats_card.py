"""Render a GitHub stats card (SVG) for the profile README.

Replaces the public github-readme-stats.vercel.app card, which is no longer served.
Usage: GITHUB_TOKEN=... python3 scripts/stats_card.py <user> <out.svg> [--dark]
"""
import json
import os
import sys
import urllib.request
from html import escape

QUERY = """
query($login: String!) {
  user(login: $login) {
    name login
    contributionsCollection { totalCommitContributions restrictedContributionsCount }
    pullRequests { totalCount }
    issues { totalCount }
    repositoriesContributedTo(includeUserRepositories: true, contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]) { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount nodes { stargazerCount }
    }
  }
}"""

THEMES = {
    "light": {"bg": "#fffefe", "border": "#e4e2e2", "title": "#2f80ed", "text": "#434d58",
              "icon": "#4c71f2"},
    "dark": {"bg": "#0d1117", "border": "#30363d", "title": "#58a6ff", "text": "#c9d1d9",
             "icon": "#79c0ff"},
}

# 16x16 Octicons paths: star, commit, pull request, issue, repo.
ICONS = {
    "star": "M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Zm0 2.445L6.615 5.5a.75.75 0 0 1-.564.41l-3.097.45 2.24 2.184a.75.75 0 0 1 .216.664l-.528 3.084 2.769-1.456a.75.75 0 0 1 .698 0l2.77 1.456-.53-3.084a.75.75 0 0 1 .216-.664l2.24-2.183-3.096-.45a.75.75 0 0 1-.564-.41L8 2.694Z",
    "commit": "M11.93 8.5a4.002 4.002 0 0 1-7.86 0H.75a.75.75 0 0 1 0-1.5h3.32a4.002 4.002 0 0 1 7.86 0h3.32a.75.75 0 0 1 0 1.5Zm-1.43-.75a2.5 2.5 0 1 0-5 0 2.5 2.5 0 0 0 5 0Z",
    "pr": "M1.5 3.25a2.25 2.25 0 1 1 3 2.122v5.256a2.251 2.251 0 1 1-1.5 0V5.372A2.25 2.25 0 0 1 1.5 3.25Zm5.677-.177L9.573.677A.25.25 0 0 1 10 .854V2.5h1A2.5 2.5 0 0 1 13.5 5v5.628a2.251 2.251 0 1 1-1.5 0V5a1 1 0 0 0-1-1h-1v1.646a.25.25 0 0 1-.427.177L7.177 3.427a.25.25 0 0 1 0-.354ZM3.75 2.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm0 9.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm8.25.75a.75.75 0 1 0 1.5 0 .75.75 0 0 0-1.5 0Z",
    "issue": "M8 9.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3ZM8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0ZM1.5 8a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0Z",
    "repo": "M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z",
}


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if body.get("errors"):
        sys.exit(f"GraphQL error: {body['errors']}")
    return body["data"]["user"]


def render(user, theme):
    c = THEMES[theme]
    cc = user["contributionsCollection"]
    rows = [
        ("star", "Total Stars Earned", sum(n["stargazerCount"] for n in user["repositories"]["nodes"])),
        ("commit", "Commits (last year)", cc["totalCommitContributions"] + cc["restrictedContributionsCount"]),
        ("pr", "Total PRs", user["pullRequests"]["totalCount"]),
        ("issue", "Total Issues", user["issues"]["totalCount"]),
        ("repo", "Contributed to (last year)", user["repositoriesContributedTo"]["totalCount"]),
    ]
    name = escape(user["name"] or user["login"])
    lines = []
    for i, (icon, label, value) in enumerate(rows):
        y = 70 + i * 25
        lines.append(
            f'<g transform="translate(25,{y})">'
            f'<path transform="translate(0,-12)" fill="{c["icon"]}" d="{ICONS[icon]}"/>'
            f'<text x="25" class="stat">{label}:</text>'
            f'<text x="240" class="stat bold">{value:,}</text></g>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="467" height="195" viewBox="0 0 467 195" role="img" aria-label="{name}'s GitHub Stats">
<style>
  .title {{ font: 600 18px 'Segoe UI', Ubuntu, 'Helvetica Neue', Sans-Serif; fill: {c["title"]}; }}
  .stat {{ font: 600 14px 'Segoe UI', Ubuntu, 'Helvetica Neue', Sans-Serif; fill: {c["text"]}; }}
  .bold {{ font-weight: 700; }}
</style>
<rect x="0.5" y="0.5" rx="4.5" width="466" height="194" fill="{c["bg"]}" stroke="{c["border"]}"/>
<text x="25" y="35" class="title">{name}'s GitHub Stats</text>
{"".join(lines)}
</svg>
'''


def main():
    login, out = sys.argv[1], sys.argv[2]
    theme = "dark" if "--dark" in sys.argv else "light"
    user = fetch(login, os.environ["GITHUB_TOKEN"])
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(render(user, theme))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
