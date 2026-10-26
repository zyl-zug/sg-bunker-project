"""
STEP 2 - Clean the raw data and turn it into one row per month.

Raw data is "long": one row per month PER fuel type.
    1995-01 | Marine Gas Oil   | 135.4
    1995-01 | Marine Diesel Oil| 67.9
We make it "wide": one row per month, one column per fuel group.
    1995-01 | HSFO | VLSFO | Distillates | Biofuel | LNG

Units: MPA figures look like THOUSAND tonnes (e.g. 67.9 = 67,900 t).
       The check at the end confirms this against a known news figure.

What it produces:
    data/bunker_clean.csv
"""

import pandas as pd

# 1. Read the raw file saved by step 1
raw = pd.read_csv("data/bunker_sales_raw.csv")

# 2. Keep the 3 useful columns, with clear names and the right types
df = pd.DataFrame({
    # "1995-01" -> a real date (1 Jan 1995), so Python can sort and plot it
    "date": pd.to_datetime(raw["month"].astype(str).str[:7], format="%Y-%m"),
    # fuel name, with stray spaces removed
    "label": raw["bunker_type"].astype(str).str.strip(),
    # sales arrive as text; turn into numbers (anything odd becomes blank)
    "kt": pd.to_numeric(raw["bunker_sales"], errors="coerce"),   # kt = thousand tonnes
})


# 3. Put each fuel name into a group.
#    ORDER MATTERS: "Low Sulphur Marine Gas Oil" contains "low sulphur",
#    but it is a gas oil (distillate), so the gas-oil rule must come first.
def to_group(label):
    s = label.lower()
    if "total" in s:
        return "DROP"                     # a total row would double-count
    if "lng" in s or "liquefied natural gas" in s:
        return "LNG"
    if "methanol" in s or "ammonia" in s:
        return "Other_alt"                # new fuels, tiny volumes
    if "bio" in s:
        return "Biofuel"                  # all bio-blended fuels
    if any(k in s for k in ["gas oil", "diesel", "mgo", "mdo", "distillate"]):
        return "Distillates"              # MGO / MDO
    if any(k in s for k in ["very low sulphur", "low sulphur", "vlsfo", "lsfo", "0.5"]):
        return "VLSFO"                    # low-sulphur fuel oil
    if any(k in s for k in ["high sulphur", "hsfo", "380", "500", "180",
                            "marine fuel oil", "mfo", "ifo"]):
        return "HSFO"                     # high-sulphur fuel oil
    return "Unmapped"                     # anything we didn't expect


df["group"] = df["label"].map(to_group)

# 4. Show which label went where - CHECK THIS LIST on the first run
print("=== Fuel label -> group ===")
for (group, label), n in df.groupby(["group", "label"]).size().items():
    print(f"{group:12} <- {label}  ({n} months)")
unmapped = df.loc[df["group"] == "Unmapped", "label"].unique()
if len(unmapped):
    print("\nWARNING - unmapped labels, add them to to_group():", list(unmapped))

# 5. Long -> wide: one row per month, one column per group (sum within group)
wide = (df[df["group"] != "DROP"]
        .pivot_table(index="date", columns="group", values="kt", aggfunc="sum")
        .sort_index()
        .fillna(0.0))
for g in ["HSFO", "VLSFO", "Distillates", "Biofuel", "LNG"]:
    if g not in wide:
        wide[g] = 0.0                     # make sure every column exists

# 6. The measures we need
wide["hsfo_vlsfo_total"] = wide["HSFO"] + wide["VLSFO"]
# Main measure: of the two fuels a scrubber ship chooses between, how much was HSFO?
wide["hsfo_share"] = wide["HSFO"] / wide["hsfo_vlsfo_total"]
wide["hsfo_share_mom_pts"] = wide["hsfo_share"].diff() * 100     # vs last month, in % points
wide["hsfo_share_yoy_pts"] = wide["hsfo_share"].diff(12) * 100   # vs same month last year
wide["is_preliminary"] = False
wide.iloc[-1, wide.columns.get_loc("is_preliminary")] = True     # latest month = estimate

# 7. Save
wide.reset_index().to_csv("data/bunker_clean.csv", index=False)
print(f"\nSaved data/bunker_clean.csv: {len(wide)} months, "
      f"{wide.index.min():%Y-%m} to {wide.index.max():%Y-%m}")

# 8. Sanity check against the news:
#    ENGINE reported Aug 2026 HSFO = 2.10 million t and VLSFO = 2.19 million t.
#    If the data is in thousand tonnes, the numbers below should be ~2,100 and ~2,190.
print("\nLast 6 months (thousand tonnes):")
print(wide[["HSFO", "VLSFO", "hsfo_share"]].tail(6).round(3))
