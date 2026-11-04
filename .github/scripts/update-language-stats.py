#!/usr/bin/env python3
import html
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


API = "https://api.github.com"
OWNER = os.environ.get("PROFILE_GITHUB_OWNER", "robsonejsoares")
PROFILE_REPO = f"{OWNER}/robsonejsoares"
PALETTE = ("#f59e0b", "#38bdf8", "#a78bfa", "#34d399", "#818cf8")


def fail(message):
    print(message, file=sys.stderr)
    raise SystemExit(1)


def api_get(path, token):
    request = urllib.request.Request(
        f"{API}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "profile-language-stats",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        fail(f"GitHub API request failed with HTTP {error.code}. Check token access and rate limits.")
    except urllib.error.URLError:
        fail("Could not reach the GitHub API.")


def get_repositories(token):
    repos = []
    page = 1
    while True:
        batch = api_get(
            "/user/repos?"
            + urllib.parse.urlencode(
                {
                    "affiliation": "owner",
                    "visibility": "all",
                    "per_page": 100,
                    "page": page,
                }
            ),
            token,
        )
        if not isinstance(batch, list):
            fail("GitHub API returned an unexpected repository list.")
        repos.extend(batch)
        if len(batch) < 100:
            return repos
        page += 1


def distribution(token):
    current_user = api_get("/user", token)
    if current_user.get("login", "").lower() != OWNER.lower():
        fail("PROFILE_STATS_TOKEN must belong to the profile owner.")

    repos = get_repositories(token)
    totals = {}
    included = 0
    for repo in repos:
        owner = repo.get("owner", {}).get("login", "")
        full_name = repo.get("full_name", "")
        if owner.lower() != OWNER.lower() or repo.get("fork") or full_name.lower() == PROFILE_REPO.lower():
            continue
        languages = api_get(f"/repos/{urllib.parse.quote(full_name, safe='/')}/languages", token)
        if not isinstance(languages, dict):
            fail("GitHub API returned unexpected language statistics.")
        included += 1
        for language, byte_count in languages.items():
            if isinstance(byte_count, int) and byte_count > 0:
                totals[language] = totals.get(language, 0) + byte_count

    if not included or not totals:
        fail("No language data found in owned repositories (excluding forks and the profile repository).")

    ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0].lower()))
    visible = ranked[:4]
    if len(ranked) > 4:
        visible.append(("Outras linguagens", sum(value for _, value in ranked[4:])))

    total_bytes = sum(value for _, value in visible)
    raw_percentages = [(name, value, value * 100 / total_bytes) for name, value in visible]
    rounded = [int(value) for _, _, value in raw_percentages]
    remainder = 100 - sum(rounded)
    order = sorted(
        range(len(raw_percentages)),
        key=lambda index: (-(raw_percentages[index][2] - rounded[index]), index),
    )
    for index in order[:remainder]:
        rounded[index] += 1

    return [
        (name, value / total_bytes, rounded[index])
        for index, (name, value, _) in enumerate(raw_percentages)
    ]


def render_rows(languages):
    rows = []
    for index, (name, ratio, percentage) in enumerate(languages):
        y = 68 + index * 24
        color = PALETTE[index % len(PALETTE)]
        label = html.escape(name)
        width = 120 * ratio
        rows.append(
            f'<circle cx="526" cy="{y}" r="4" fill="{color}"/>'
            f'<text class="lb" x="538" y="{y + 4}" font-size="10.5">{label}</text>'
            f'<rect class="track" x="680" y="{y - 3}" width="120" height="6" rx="3"/>'
            f'<rect x="680" y="{y - 3}" width="{width:.2f}" height="6" rx="3" fill="{color}"/>'
            f'<text x="838" y="{y + 4}" text-anchor="end" font-size="10.5" '
            f'font-weight="700" fill="{color}">{percentage}%</text>'
        )
    return "\n  ".join(rows)


def main():
    token = os.environ.get("PROFILE_STATS_TOKEN")
    if not token:
        fail("Set the PROFILE_STATS_TOKEN Actions secret to a read-only token for all owned repositories.")

    path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "dashboard.svg")
    path = os.path.normpath(path)
    with open(path, encoding="utf-8") as dashboard_file:
        svg = dashboard_file.read()

    start = "<!-- LANGUAGE_ROWS_START -->"
    end = "<!-- LANGUAGE_ROWS_END -->"
    if svg.count(start) != 1 or svg.count(end) != 1:
        fail("Could not find the language rows markers in assets/dashboard.svg.")

    rows = render_rows(distribution(token))
    before, remainder = svg.split(start, 1)
    _, after = remainder.split(end, 1)
    with open(path, "w", encoding="utf-8") as dashboard_file:
        dashboard_file.write(f"{before}{start}\n  {rows}\n  {end}{after}")

    print("Updated language percentages in assets/dashboard.svg.")


if __name__ == "__main__":
    main()
