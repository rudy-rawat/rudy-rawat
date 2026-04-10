import os, requests

GITHUB_USER = os.getenv("GITHUB_USER", os.getenv("GITHUB_REPOSITORY", "rudy-rawat/rudy-rawat").split("/")[0])
DISPLAY_TEXT = os.getenv("PULSE_TEXT", "RUDY RAWAT").upper()

# Light mode color palette (clean neutrals with blue accent)
COLORS = [
    "#ffffff",  # background
  "rgba(0,114,255,0.05)",
  "rgba(0,114,255,0.12)",
  "rgba(0,114,255,0.22)",
  "rgba(0,114,255,0.35)",
  "rgba(0,114,255,0.55)",
  "#0072ff",  # max intensity
]

THRESHOLDS = [0, 1, 2, 4, 8, 12, 20]

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
    for idx, th in enumerate(THRESHOLDS):
        if count < th:
            return COLORS[idx - 1]
    return COLORS[-1]

def main():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Missing GITHUB_TOKEN")
  print(f"Rendering pulse text: {DISPLAY_TEXT}")

    resp = requests.post(
        "https://api.github.com/graphql",
        json={"query": QUERY, "variables": {"login": GITHUB_USER}},
        headers={"Authorization": f"bearer {token}"}
    ).json()

    weeks = resp["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

    wc = len(weeks)
    mask_base = build_mask_base(DISPLAY_TEXT)
    glyph_width = max((x for x, _ in mask_base), default=0) + 1
    x_shift = max((wc - glyph_width) // 2, 0)
    mask = {
      (x + x_shift, y + 1)
      for (x, y) in mask_base
      if (x + x_shift) < wc and (y + 1) < 7
    }

    CELL, GAP = 14, 3
    W = wc * (CELL + GAP)
    H = 7 * (CELL + GAP)

    svg = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" '
           f'xmlns="http://www.w3.org/2000/svg">']

    svg.append("""
<defs>
  <pattern id="pixelGrid" width="7" height="7" patternUnits="userSpaceOnUse">
    <rect width="7" height="7" fill="none" stroke="rgba(0,0,0,0.05)" stroke-width="0.4"/>
  </pattern>

  <style>
    @keyframes pulse {
      0%,100% { opacity: 1; filter: drop-shadow(0 0 2px currentColor); }
      92% { opacity: .9; filter: drop-shadow(0 0 5px currentColor); }
      96% { opacity: .5; filter: drop-shadow(0 0 1px currentColor); }
    }
    .cell {
      animation: pulse 2s infinite linear;
      shape-rendering: crispEdges;
    }
  </style>
</defs>
""")

    for x, week in enumerate(weeks):
        base_x = x * (CELL + GAP)
        for y, day in enumerate(week["contributionDays"]):
            base_y = y * (CELL + GAP)
            color = pick_color(day["contributionCount"])
            delay = (x * 7 + y) * 0.0113
            active = (x, y) in mask

            # main cell
            svg.append(
                f'<rect class="cell" x="{base_x}" y="{base_y}" width="{CELL}" height="{CELL}" '
                f'fill="{color}" style="animation-delay:{delay}s" />'
            )

            # subtle grid overlay
            svg.append(
                f'<rect x="{base_x}" y="{base_y}" width="{CELL}" height="{CELL}" fill="url(#pixelGrid)" />'
            )

            # highlight stroke for mask cells (dark stroke on light background)
            if active:
                svg.append(
                    f'<rect x="{base_x}" y="{base_y}" width="{CELL}" height="{CELL}" '
                f'fill="none" stroke="#003f91" stroke-width="1.2"/>'
                )

    svg.append("</svg>")

    os.makedirs("dist", exist_ok=True)
    with open("dist/heartbeat-light.svg", "w") as f:
        f.write("\n".join(svg))

    print("✅ Light mode SVG generated: dist/heartbeat-light.svg")

if __name__ == "__main__":
    main()
