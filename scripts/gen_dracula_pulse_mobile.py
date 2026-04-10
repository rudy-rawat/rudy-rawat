import os, requests

GITHUB_USER = os.getenv("GITHUB_USER", os.getenv("GITHUB_REPOSITORY", "rudy-rawat/rudy-rawat").split("/")[0])
DISPLAY_TEXT = os.getenv("PULSE_TEXT", "RUDY RAWAT").upper()

COLORS = [
    "#0d1117",
  "rgba(0,229,255,0.14)",
  "rgba(0,229,255,0.22)",
  "rgba(0,229,255,0.34)",
  "rgba(0,229,255,0.52)",
  "rgba(0,229,255,0.72)",
  "#00e5ff",
]

THRESHOLDS = [0,1,2,4,8,12,20]

FONT_4X5 = {
  "R": ["1110", "1001", "1110", "1010", "1001"],
  "U": ["1001", "1001", "1001", "1001", "1111"],
  "D": ["1110", "1001", "1001", "1001", "1110"],
  "Y": ["1001", "1001", "0110", "0010", "0010"],
  "A": ["0110", "1001", "1111", "1001", "1001"],
  "W": ["1001", "1001", "1011", "1111", "1001"],
  "T": ["1111", "0010", "0010", "0010", "0010"],
  " ": ["00", "00", "00", "00", "00"],
  "-": ["000", "111", "000", "000", "000"],
}

def build_mask_base(text):
  mask = set()
  x_cursor = 0
  for ch in text:
    glyph = FONT_4X5.get(ch, FONT_4X5[" "])
    width = len(glyph[0])
    for y, row in enumerate(glyph):
      for x, pixel in enumerate(row):
        if pixel == "1":
          mask.add((x_cursor + x, y))
    x_cursor += width + 1
  return mask

QUERY = """
query ($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            weekday
            contributionCount
          }
        }
      }
    }
  }
}
"""

def pick_color(count):
    for idx, t in enumerate(THRESHOLDS):
        if count < t: return COLORS[idx-1]
    return COLORS[-1]

def main():
    token = os.getenv("GITHUB_TOKEN")
    if not token: raise SystemExit("Missing GITHUB_TOKEN")
    print(f"Rendering pulse text: {DISPLAY_TEXT}")

    resp = requests.post(
        "https://api.github.com/graphql",
        json={"query": QUERY, "variables": {"login": GITHUB_USER}},
        headers={"Authorization": f"bearer {token}"}
    ).json()

    weeks = resp["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

    week_count = len(weeks)
    mask_base = build_mask_base(DISPLAY_TEXT)
    glyph_width = max((x for x, _ in mask_base), default=0) + 1
    x_shift = max((week_count - glyph_width) // 2, 0)
    mask = {
      (x + x_shift, y + 1)
      for (x, y) in mask_base
      if (x + x_shift) < week_count and (y + 1) < 7
    }

    CELL, GAP = 10, 2

    w = week_count * (CELL + GAP)
    h = 7 * (CELL + GAP)

    svg = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none" xmlns="http://www.w3.org/2000/svg">']

    svg.append("""
<style>
.cell {
  shape-rendering:crispEdges;
  animation:pulse 1.8s infinite ease-in-out;
}
@keyframes pulse {
  0%,100% { opacity:1; }
  90% { opacity:.7; }
}
</style>
<g>
""")

    for x, week in enumerate(weeks):
        base_x = x * (CELL + GAP)
        for y, day in enumerate(week["contributionDays"]):
            base_y = y * (CELL + GAP)
            color = pick_color(day["contributionCount"])
            delay = (x * 7 + y) * 0.012  # slower pulse feels better on mobile
            is_mask = (x, y) in mask

            svg.append(
                f'<rect class="cell" x="{base_x}" y="{base_y}" width="{CELL}" height="{CELL}" '
                f'fill="{color}" style="animation-delay:{delay}s"/>'
            )

            if is_mask:
                svg.append(
                    f'<rect x="{base_x}" y="{base_y}" width="{CELL}" height="{CELL}" '
                f'fill="none" stroke="#7ef9ff" stroke-width="1"/>'
                )

    svg.append("</g></svg>")

    os.makedirs("dist", exist_ok=True)
    with open("dist/heartbeat-dracula-mobile.svg", "w") as f:
        f.write("\n".join(svg))

    print("📱✅ Mobile SVG generated: dist/heartbeat-dracula-mobile.svg")

if __name__ == "__main__":
    main()
