"""
STEP 3 (ggplot version) - Charts A, B, C, D with plotnine (ggplot2 style for Python).

Install once:   pip install plotnine
Needs:          data/bunker_clean.csv, data/hi5_spread_manual.csv, data/hi5_annual.csv
Run as cells (like RStudio): click "Run Cell" above any "# %%" line in VS Code.
Produces:       data/gg_A_trend.png, gg_B_share_vs_spread.png, gg_C_tonnes.png, gg_D_annual.png
"""
# %% Setup: libraries and data
import os
import warnings
import pandas as pd
warnings.filterwarnings("ignore", message="Could not infer format")
from plotnine import (ggplot, aes, geom_line, geom_point, geom_path, geom_text,
                      geom_vline, annotate, facet_wrap, labs, theme_minimal,
                      theme, element_text, scale_color_manual,
                      scale_shape_manual, scale_fill_manual, scale_x_reverse)


def to_month(series):
    """Turn any date text into the 1st of its month.
    Fixes the Excel problem: Excel saves '2026-01-01' as '1/1/26' (day/month/year),
    which Python otherwise reads as month/day/year - so months stop matching."""
    s = series.astype(str)
    dayfirst = s.str.contains("/").any()
    d = pd.to_datetime(s, dayfirst=dayfirst, errors="coerce")
    return d.dt.to_period("M").dt.to_timestamp()


clean = pd.read_csv("data/bunker_clean.csv")
clean["date"] = to_month(clean["date"])
prices = pd.read_csv("data/hi5_spread_manual.csv")
prices["date"] = to_month(prices["month"])
# Rows WITH a source link = "sourced"; rows WITHOUT = "assumed" (your estimates).
# Both are charted, but assumed points are drawn hollow so nobody mistakes them for real data.
prices["data_type"] = prices["source_url"].astype(str).str.startswith("http").map(
    {True: "sourced", False: "assumed"})
prices["spread_usd_t"] = prices["vlsfo_usd_t"] - prices["hsfo_usd_t"]
neg = prices[prices["spread_usd_t"] < 0]
if len(neg):
    print("WARNING - negative spread (HSFO dearer than VLSFO) in:",
          [d.strftime("%Y-%m") for d in neg["date"]], "- check these assumptions")
annual = pd.read_csv("data/hi5_annual.csv") if os.path.exists("data/hi5_annual.csv") else None

COLORS = {"HSFO": "#c0392b", "VLSFO": "#2e6da4"}
base = theme_minimal() + theme(figure_size=(10, 4), plot_title=element_text(weight="bold"))

# %% A. HSFO share since 2020 ------------------------------------------------
a = clean[clean["date"] >= "2020-01-01"].assign(share_pct=lambda d: d["hsfo_share"] * 100)
pA = (ggplot(a, aes("date", "share_pct"))
      + geom_line(color=COLORS["HSFO"])
      + geom_vline(xintercept=pd.Timestamp("2026-03-01"), linetype="dashed", color="grey")
      + annotate("text", x=pd.Timestamp("2026-03-01"), y=a["share_pct"].max(),
                 label="Iran war ", ha="right", size=8)
      + labs(title="A. HSFO share of HSFO + VLSFO sales, Singapore (since IMO 2020)",
             x="", y="HSFO share, %")
      + base)
pA.save("data/gg_A_trend.png", dpi=150, verbose=False)
pA   # <- shows the chart when run as a cell

# %% B. share vs spread (sourced = solid dots, assumed = hollow dots) ----------
b = clean.merge(prices[["date", "spread_usd_t", "data_type"]], on="date").dropna(subset=["spread_usd_t"])
long_b = pd.concat([
    pd.DataFrame({"date": b["date"], "value": b["hsfo_share"] * 100,
                  "series": "HSFO share, % (MPA, all real)", "data_type": "sourced"}),
    pd.DataFrame({"date": b["date"], "value": b["spread_usd_t"],
                  "series": "Hi-5 spread, $/t", "data_type": b["data_type"]}),
])
n_src = (b["data_type"] == "sourced").sum()
print(f"Chart B: {len(b)} months ({n_src} sourced, {len(b) - n_src} assumed)")
pB = (ggplot(long_b, aes("date", "value"))
      + geom_line(color="grey")
      + geom_point(aes(shape="data_type", fill="data_type"), size=2.5, color="black")
      + scale_shape_manual(values={"sourced": "o", "assumed": "o"})
      + scale_fill_manual(values={"sourced": "black", "assumed": "white"})
      + facet_wrap("~series", ncol=1, scales="free_y")
      + labs(title="B. HSFO share vs Hi-5 spread", x="", y="", shape="", fill="",
             caption=f"Hollow dots = assumed prices (not sourced). Sourced months: {n_src}")
      + base + theme(figure_size=(10, 5)))
pB.save("data/gg_B_share_vs_spread.png", dpi=150, verbose=False)
pB   # <- shows the chart when run as a cell

# %% C. tonnes since 2024 -------------------------------------------------------
c = clean[clean["date"] >= "2024-01-01"].melt(
    id_vars="date", value_vars=["HSFO", "VLSFO"], var_name="fuel", value_name="kt")
c["mt"] = c["kt"] / 1000                       # thousand tonnes -> million tonnes
pC = (ggplot(c, aes("date", "mt", color="fuel"))
      + geom_line() + geom_point(size=1.5)
      + scale_color_manual(values=COLORS)
      + labs(title="C. VLSFO vs HSFO sold in Singapore", x="", y="Million tonnes", color="")
      + base)
pC.save("data/gg_C_tonnes.png", dpi=150, verbose=False)
pC   # <- shows the chart when run as a cell

# %% D. Yearly spread vs share
if annual is None:
    print("Skipped chart D: data/hi5_annual.csv not found.")
else:
    # ---- D. yearly: spread vs share, as a connected scatter ----------------------------
    clean["year"] = clean["date"].dt.year
    yr = clean.groupby("year")[["HSFO", "hsfo_vlsfo_total"]].sum()
    yr["share_pct"] = yr["HSFO"] / yr["hsfo_vlsfo_total"] * 100
    d = annual.merge(yr["share_pct"].reset_index(), on="year").sort_values("year")
    print(d[["year", "hi5_avg_usd_t", "share_pct"]].round(1).to_string(index=False))
    pD = (ggplot(d, aes("hi5_avg_usd_t", "share_pct"))
          + geom_path(color="grey", arrow=None)
          + scale_x_reverse()   # 2022 (wide spread) on the left, 2025 (narrow) on the right
          + geom_point(size=3, color=COLORS["HSFO"])
          + geom_text(aes(label="year"), nudge_y=(d["share_pct"].max() - d["share_pct"].min()) * 0.06 + 0.01, size=9)
          + labs(title="2022–25: spread fell, HSFO share did not",
                 x="Hi-5 spread, $/t (Platts yearly average; axis reversed so years run left to right)",
                 y="HSFO share, %")
          + base + theme(figure_size=(8, 5)))
    pD.save("data/gg_D_annual.png", dpi=150, verbose=False)

pD if annual is not None else None   # <- shows the chart when run as a cell

# %% Done
print("Saved charts in the data folder.")