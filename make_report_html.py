"""
STEP 5 - One-page HTML report: takeaways + 4 interactive charts.

Run:      python make_report_html.py
Output:   report/bunker_report.html  (double-click to open; needs internet for fonts/charts)
Edit:     the TEXT block below - your headline, takeaways and chart notes.
          Numbers in {curly braces} are filled in automatically from your data.
"""
import os
import warnings
from datetime import date

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore", message="Could not infer format")

# ============================ EDIT YOUR WORDS HERE ============================
TEXT = {
    "title": "Singapore's HSFO demand is outgrowing the price signal",
    "standfirst": ("HSFO's share of Singapore fuel-oil sales rose from {share_first:.0f}% in "
                   "{first_year} to {share_ytd:.0f}% in {ytd_year} year to date, and kept rising "
                   "while the Hi-5 spread narrowed from ${hi5_first:.0f}/t to ${hi5_last:.0f}/t "
                   "({hi5_first_year}–{hi5_last_year})."),
    "takeaways": [
        "The rise is consistent with structural demand from scrubber-fitted ships, not with the spread alone.",
        "In 2026, HSFO tonnes rose while VLSFO fell: ships switched fuel rather than VLSFO buyers leaving Singapore.",
        "Watch next: whether the narrower spread seen in October 2026 pulls HSFO share back down in the next MPA releases.",
    ],
    "notes": {
        "D": "Each dot is one year, from 2022 on the left to 2025 on the right. The spread got smaller every year, yet the share did not fall with it.",
        "A": "Share of HSFO in HSFO + VLSFO sales since IMO 2020. The rise began before the March 2026 war.",
        "C": "Tonnes, not share: HSFO up and VLSFO down at the same time points to switching, not leakage.",
        "B": "Monthly view. Solid dots are sourced prices; hollow dots are assumptions and are not used for conclusions.",
    },
    "limits": [
        "Free monthly HSFO prices are not available; yearly Hi-5 averages come from Platts via S&P Global.",
        "Four yearly points can show a pattern, not prove cause. Scrubber-fleet data was not available.",
        "Sales cover Singapore only; buyers refuelling at other ports are not visible. The latest month is preliminary.",
        "Month-by-month price effects can't be tested: only two months have sourced HSFO prices.",
    ],
    "sources": {
        "mpa": ("MPA monthly bunker sales, data.gov.sg",
                "https://data.gov.sg/datasets/d_4f5abbf4486bf8e52bbed3be56dde562/view"),   # check link opens
        "platts": ("Platts yearly Hi-5 averages, via S&P Global (Dec 2025)",
                   "https://www.spglobal.com/energy/en/news-research/latest-news/refined-products/122325-commodities-2026-bunker-demand-to-buoy-asias-hsfo-market-ample-supply-likely-to-cap-major-upsides"),
        "snb": ("Ship & Bunker monthly Singapore analysis",
                "https://shipandbunker.com/news/apac/537117-analysis-singapore-bunker-sales-continue-at-record-pace-despite-hormuz-crisis"),
    },
    "github": "https://github.com/zyl-zug/sg-bunker-project",   # <- your repo link
    "author": "Zhengyan LU",
}
SHOW_CHART_B = False   # monthly chart; off because only 2 months have sourced prices
# ===============================================================================

HSFO, VLSFO, MUTED, INK = "#a35c00", "#2b6cb0", "#8a94a3", "#18222d"


def to_month(series):
    s = series.astype(str)
    d = pd.to_datetime(s, dayfirst=s.str.contains("/").any(), errors="coerce")
    return d.dt.to_period("M").dt.to_timestamp()


# ---- data --------------------------------------------------------------------------
clean = pd.read_csv("data/bunker_clean.csv")
clean["date"] = to_month(clean["date"])
clean["share_pct"] = clean["hsfo_share"] * 100
clean["year"] = clean["date"].dt.year

yr = clean[clean["year"] >= 2020].groupby("year")[["HSFO", "hsfo_vlsfo_total"]].sum()
yr["share_pct"] = yr["HSFO"] / yr["hsfo_vlsfo_total"] * 100

prices = pd.read_csv("data/hi5_spread_manual.csv")
prices["date"] = to_month(prices["month"])
prices["spread"] = prices["vlsfo_usd_t"] - prices["hsfo_usd_t"]
prices["kind"] = prices["source_url"].astype(str).str.startswith("http").map(
    {True: "sourced", False: "assumed"})

annual = pd.read_csv("data/hi5_annual.csv") if os.path.exists("data/hi5_annual.csv") else None

facts = {
    "first_year": int(yr.index.min()), "share_first": yr["share_pct"].iloc[0],
    "ytd_year": int(yr.index.max()), "share_ytd": yr["share_pct"].iloc[-1],
}
if annual is not None:
    facts.update(hi5_first=annual["hi5_avg_usd_t"].iloc[0], hi5_last=annual["hi5_avg_usd_t"].iloc[-1],
                 hi5_first_year=int(annual["year"].iloc[0]), hi5_last_year=int(annual["year"].iloc[-1]))


# ---- chart styling shared by all charts ------------------------------------------
def style(fig, height=360):
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Public Sans, Helvetica, Arial, sans-serif", size=13, color=INK),
        legend=dict(orientation="h", y=1.08, x=0), hoverlabel=dict(font_size=13),
    )
    fig.update_xaxes(showgrid=False, linecolor=MUTED)
    fig.update_yaxes(gridcolor="rgba(138,148,163,0.25)", zeroline=False)
    return fig


charts = {}

# D. yearly spread vs share
if annual is not None:
    d = annual.merge(yr["share_pct"].reset_index(), on="year").sort_values("year")
    figD = go.Figure(go.Scatter(
        x=d["hi5_avg_usd_t"], y=d["share_pct"], mode="lines+markers+text", text=d["year"],
        textposition="top center", line=dict(color=MUTED, width=1.5),
        marker=dict(color=HSFO, size=12),
        hovertemplate="%{text}<br>Hi-5 spread: $%{x:.0f}/t (Platts)<br>HSFO share: %{y:.1f}% (MPA)<extra></extra>"))
    figD.update_xaxes(title="Hi-5 spread, $/t (Platts yearly average; axis reversed so years run left to right)",
                      autorange="reversed")
    figD.update_yaxes(title="HSFO share, %")
    charts["D"] = ("2022–25: spread fell, share did not", style(figD))

# A. share since 2020
a = clean[clean["date"] >= "2020-01-01"]
figA = go.Figure(go.Scatter(x=a["date"], y=a["share_pct"], mode="lines", line=dict(color=HSFO, width=2),
                            hovertemplate="%{x|%b %Y}<br>HSFO share: %{y:.1f}%<extra></extra>"))
figA.add_vline(x=pd.Timestamp("2026-03-01").timestamp() * 1000, line_dash="dot", line_color=MUTED,
               annotation_text="Iran war", annotation_font_color=INK)
figA.update_yaxes(title="HSFO share, %")
charts["A"] = ("HSFO share since IMO 2020", style(figA))

# C. tonnes since 2024
c = clean[clean["date"] >= "2024-01-01"]
figC = go.Figure()
for col, colour in [("VLSFO", VLSFO), ("HSFO", HSFO)]:
    figC.add_trace(go.Scatter(x=c["date"], y=c[col] / 1000, name=col, mode="lines+markers",
                              line=dict(color=colour, width=2), marker=dict(size=5),
                              hovertemplate="%{x|%b %Y}<br>" + col + ": %{y:.2f}m t<extra></extra>"))
figC.update_yaxes(title="Million tonnes")
charts["C"] = ("Tonnes sold: HSFO vs VLSFO", style(figC))

# B. monthly share vs spread
b = clean.merge(prices[["date", "spread", "kind", "source_url"]], on="date").dropna(subset=["spread"])
figB = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                     subplot_titles=("HSFO share, %", "Hi-5 spread, $/t"))
figB.add_trace(go.Scatter(x=b["date"], y=b["share_pct"], mode="lines+markers", name="HSFO share",
                          line=dict(color=HSFO), showlegend=False,
                          hovertemplate="%{x|%b %Y}<br>%{y:.1f}%<extra></extra>"), row=1, col=1)
figB.add_trace(go.Scatter(x=b["date"], y=b["spread"], mode="lines", line=dict(color=MUTED, width=1),
                          showlegend=False, hoverinfo="skip"), row=2, col=1)
for kind, sym in [("sourced", "circle"), ("assumed", "circle-open")]:
    p = b[b["kind"] == kind]
    figB.add_trace(go.Scatter(x=p["date"], y=p["spread"], mode="markers", name=f"Spread, {kind}",
                              marker=dict(symbol=sym, size=10, color=VLSFO, line=dict(color=VLSFO, width=2)),
                              hovertemplate="%{x|%b %Y}<br>$%{y:.0f}/t (" + kind + ")<extra></extra>"),
                   row=2, col=1)
figB.update_annotations(font=dict(size=12, color=INK))
figB = style(figB, height=440)
figB.update_layout(legend=dict(y=1.2), margin=dict(t=40))
charts["B"] = ("Monthly share vs spread", figB)

# ---- HTML ------------------------------------------------------------------------------
try:
    standfirst = TEXT["standfirst"].format(**facts)
except KeyError:
    standfirst = TEXT["standfirst"].split(", and kept")[0].format(**facts) + "."

takeaways = "\n".join(f"<li>{t}</li>" for t in TEXT["takeaways"])
limits = "\n".join(f"<li>{t}</li>" for t in TEXT["limits"])
order = ["D", "A", "C"] + (["B"] if SHOW_CHART_B else [])
CHART_SOURCES = {"D": ["platts", "mpa"], "A": ["mpa"], "C": ["mpa"], "B": ["mpa", "snb"]}
figures = ""
for i, key in enumerate(k for k in order if k in charts):
    title, fig = charts[key]
    div = fig.to_html(full_html=False, include_plotlyjs=False,
                      config={"displaylogo": False, "responsive": True,
                              "modeBarButtonsToRemove": ["lasso2d", "select2d"]})
    src = " and ".join(f'<a href="{TEXT["sources"][k][1]}">{TEXT["sources"][k][0]}</a>'
                       for k in CHART_SOURCES[key])
    figures += f"""
    <section class="chart" id="chart-{i + 1}">
      <div class="plot">{div}</div>
      <div class="note">
        <h2><span class="key">{i + 1}</span>{title}</h2>
        <p>{TEXT['notes'][key]}</p>
        <p class="src">Source: {src}</p>
      </div>
    </section>"""

used_sources = [k for k in TEXT["sources"] if any(k in CHART_SOURCES[c] for c in order if c in charts)]

html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TEXT['title']}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600&family=Public+Sans:wght@400;600&display=swap" rel="stylesheet">
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  :root {{
    --paper: #f5f7f9; --ink: #18222d; --muted: #5b6675; --rule: #d6dce3;
    --hsfo: {HSFO}; --vlsfo: {VLSFO}; --panel: #ffffff;
    color-scheme: light;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--paper); color: var(--ink);
          font: 400 16px/1.6 "Public Sans", Helvetica, Arial, sans-serif; }}
  main {{ max-width: 76rem; margin: 0 auto; padding: 2.5rem 1.5rem 3rem; }}
  .context {{ color: var(--ink); font-size: 0.9rem; margin: 0 0 1rem; }}

  h1 {{ font: 600 clamp(1.9rem, 3.6vw, 2.8rem)/1.1 "Newsreader", Georgia, serif;
        letter-spacing: -0.015em; margin: 0 0 1rem; }}
  .standfirst {{ font: 500 1.2rem/1.5 "Newsreader", Georgia, serif; margin: 0 0 1.75rem;
                 border-left: 4px solid var(--hsfo); padding-left: 1rem; max-width: 52rem; }}

  /* two equal panels: tells | can't tell */
  .panels {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
  .panel {{ background: var(--panel); padding: 1.25rem 1.5rem; border-top: 3px solid var(--hsfo); }}
  .panel.cannot {{ border-top-color: var(--muted); }}
  .panel h2 {{ font: 600 1.15rem/1.3 "Newsreader", Georgia, serif; margin: 0 0 0.6rem; }}
  .panel ul {{ margin: 0; padding-left: 1.2rem; }}
  .panel li {{ margin-bottom: 0.5rem; }}
  .tells li::marker {{ color: var(--hsfo); }}
  .cannot ul {{ color: var(--ink); }}
  .legend-note {{ color: var(--ink); font-size: 0.95rem; margin: 1rem 0 2rem; }}
  .legend-note b.h {{ color: var(--hsfo); }} .legend-note b.v {{ color: var(--vlsfo); }}

  /* charts: every chart on a white panel, plot (left) | note (right) */
  section.chart {{ display: grid; grid-template-columns: minmax(0, 2.4fr) minmax(0, 1fr);
                   gap: 2rem; align-items: center; background: var(--panel);
                   border-top: 3px solid var(--hsfo); padding: 1.25rem 1.5rem;
                   margin-bottom: 1.5rem; }}
  .note h2 {{ font: 600 1.3rem/1.3 "Newsreader", Georgia, serif; margin: 0 0 0.5rem;
              display: flex; gap: 0.6rem; align-items: baseline; }}
  .note p {{ color: var(--ink); margin: 0 0 0.75rem; }}
  .note p.src {{ font-size: 0.85rem; margin: 0; }}
  .key {{ font: 600 0.85rem/1 "Public Sans", sans-serif; color: var(--panel); background: var(--ink);
          padding: 0.3rem 0.55rem; border-radius: 3px; }}
  .plot {{ min-width: 0; }}
  footer {{ color: var(--ink); font-size: 0.9rem; border-top: 1px solid var(--rule);
            margin-top: 1.5rem; padding-top: 1rem; }}
  a {{ color: var(--vlsfo); }} a:focus-visible {{ outline: 2px solid var(--hsfo); outline-offset: 2px; }}

  @media (max-width: 860px) {{
    .panels, section.chart {{ grid-template-columns: 1fr; gap: 1.25rem; }}
    section.chart .note {{ order: -1; }}
  }}
</style>
</head>
<body>
<main>
  <p class="context">Singapore bunker fuel analysis for a heavies desk, {date.today():%B %Y}</p>
  <h1>{TEXT['title']}</h1>
  <p class="standfirst">{standfirst}</p>
  <div class="panels">
    <div class="panel tells">
      <h2>What this analysis tells you</h2>
      <ul>
        {takeaways}
      </ul>
    </div>
    <div class="panel cannot">
      <h2>What it can't tell you</h2>
      <ul>
        {limits}
      </ul>
    </div>
  </div>
  <p class="legend-note">In every chart, <b class="h">amber is HSFO</b> and <b class="v">blue is VLSFO</b>. Hover over any point to see its value and source.</p>
  {figures}
  <footer>
    <p>Sources: {"; ".join(f'<a href="{TEXT["sources"][k][1]}">{TEXT["sources"][k][0]}</a>' for k in used_sources)}.
       HSFO share = HSFO ÷ (HSFO + VLSFO), from MPA tonnes.</p>
    <p>{TEXT["author"]}. <a href="{TEXT["github"]}">Code and data on GitHub</a></p>
  </footer>
</main>
</body>
</html>"""

os.makedirs("report", exist_ok=True)
with open("report/bunker_report.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Saved report/bunker_report.html - double-click it to open in your browser.")