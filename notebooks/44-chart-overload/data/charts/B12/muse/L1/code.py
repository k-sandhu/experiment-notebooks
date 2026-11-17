import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")
df["date"] = pd.to_datetime(df["month"])
df["days"] = df["date"].dt.days_in_month

# Restriction period: June-September
rest = df[df["date"] >= "2026-06-01"].copy()
rest["excess_ml"] = (
    (rest["litres_per_household_day"] - rest["target_lphd"])
    * rest["households"] * rest["days"] / 1e6
)

rows = []
for district, g in rest.groupby("district"):
    avg = np.average(g["litres_per_household_day"], weights=g["days"])
    target = g["target_lphd"].iloc[0]
    rows.append({
        "district": district,
        "avg": avg,
        "target": target,
        "pct_over": (avg / target - 1) * 100,
        "excess_ml": g["excess_ml"].sum(),
    })

s = pd.DataFrame(rows).sort_values("pct_over", ascending=True).reset_index(drop=True)

# Hillcrest meter-adjusted figure: new meters from July read ~8% high
hc = rest[rest["district"] == "Hillcrest"].copy()
hc["adj_lphd"] = np.where(
    hc["date"] >= "2026-07-01",
    hc["litres_per_household_day"] / 1.08,
    hc["litres_per_household_day"],
)
hc_adj_avg = np.average(hc["adj_lphd"], weights=hc["days"])
hc_target = hc["target_lphd"].iloc[0]
hc_adj_pct = (hc_adj_avg / hc_target - 1) * 100
hc_row = s[s["district"] == "Hillcrest"].iloc[0]

# Colours: Hillcrest stands out, small overshoots amber, compliant districts muted teal
colors = []
for _, r in s.iterrows():
    if r["district"] == "Hillcrest":
        colors.append("#C1272D")
    elif r["pct_over"] > 0:
        colors.append("#E69F00")
    else:
        colors.append("#3A7CA5")

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(left=0.17, right=0.96, top=0.80, bottom=0.16)

y = np.arange(len(s))
ax.barh(y, s["pct_over"], height=0.58, color=colors, edgecolor="white", zorder=3)
ax.axvline(0, color="black", linewidth=1.4, zorder=4)

ax.set_yticks(y)
ax.set_yticklabels(s["district"], fontsize=12)
for label, district in zip(ax.get_yticklabels(), s["district"]):
    if district == "Hillcrest":
        label.set_fontweight("bold")
        label.set_color("#C1272D")

ax.set_xlim(-11, 28)
ax.set_xticks([-10, -5, 0, 5, 10, 15, 20, 25])
ax.set_xticklabels(["-10%", "-5%", "TARGET", "+5%", "+10%", "+15%", "+20%", "+25%"], fontsize=11)
ax.set_xlabel("Jun–Sep use per household vs restriction target", fontsize=12)
ax.xaxis.grid(True, color="#CCCCCC", linewidth=0.7, linestyle="--", zorder=0)
ax.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)
ax.tick_params(length=0)

# Value labels on every bar
for yi, (_, r) in zip(y, s.iterrows()):
    label = f"{r['pct_over']:+.0f}%  ({r['avg']:.0f} vs {r['target']:.0f} L/day)"
    if r["pct_over"] >= 0:
        ax.text(r["pct_over"] + 0.5, yi, label, va="center", ha="left",
                fontsize=10.5,
                fontweight="bold" if r["district"] == "Hillcrest" else "normal",
                color="#C1272D" if r["district"] == "Hillcrest" else "black")
    else:
        ax.text(r["pct_over"] - 0.5, yi, label, va="center", ha="right", fontsize=10.5)

# Meter-corrected Hillcrest marker — correction does not explain the gap
hc_y = y[s["district"] == "Hillcrest"][0]
ax.plot(hc_adj_pct, hc_y, marker="D", markersize=9,
        markerfacecolor="white", markeredgecolor="black", markeredgewidth=1.6, zorder=5)
ax.annotate(f"After 8% meter correction: still {hc_adj_pct:+.0f}%\n"
            f"≈{hc_row['excess_ml']:.0f} ML over target in Jun–Sep",
            xy=(hc_adj_pct, hc_y), xytext=(hc_adj_pct - 1, hc_y - 1.35),
            fontsize=10, ha="left", va="center",
            arrowprops=dict(arrowstyle="->", color="black", lw=1.2),
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="black", lw=0.9))

fig.text(0.17, 0.94, "Focus enforcement on Hillcrest — the only district far above target",
         fontsize=17, fontweight="bold", ha="left", va="center")
fig.text(0.17, 0.885,
         "All other districts are at or below their target under restrictions (Jun–Sep 2026)",
         fontsize=12, ha="left", va="center", color="#333333")
fig.text(0.17, 0.03,
         "Target = 20% below Apr–May use per household.  Bars show Jun–Sep average litres per household per day vs target.",
         fontsize=9, ha="left", va="center", color="#666666")
