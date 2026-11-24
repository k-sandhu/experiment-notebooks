import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")
df["late"] = df["late"].astype(str).str.lower().eq("true")

LIMIT = 48
couriers = ["Swiftline", "Northway", "ParcelPro"]
ypos = {c: i for i, c in enumerate(reversed(couriers))}  # Swiftline at top

def wilson(k, n, z=1.96):
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return p, max(0, centre - half), centre + half

stats = {}
for c in couriers:
    d = df[df["courier"] == c]
    k = int((d["actual_hours"] > LIMIT).sum())
    n = len(d)
    p, lo, hi = wilson(k, n)
    stats[c] = dict(k=k, n=n, p=p, lo=lo, hi=hi,
                    median=d["actual_hours"].median(),
                    cost=d["cost_usd"].mean())

RED = "#c0392b"
GREY = "#8c8c8c"
DARK = "#2b2b2b"

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), sharey=True,
    gridspec_kw={"width_ratios": [1.7, 1], "wspace": 0.08}
)
fig.subplots_adjust(left=0.12, right=0.97, top=0.78, bottom=0.14)

# ---- Left panel: every delivery, with the 48 h cold-pack limit
rng = np.random.default_rng(1)
xmax = max(80, df["actual_hours"].max() + 4)
ax1.axvspan(LIMIT, xmax, color=RED, alpha=0.07, zorder=0)
ax1.axvline(LIMIT, color=RED, lw=1.5, ls="--", zorder=1)
ax1.text(LIMIT + 1, 2.45, "Cold packs fail\nafter 48 h", color=RED,
         fontsize=10, va="top", ha="left", fontweight="bold")

for c in couriers:
    d = df[df["courier"] == c]
    y = ypos[c] + rng.uniform(-0.22, 0.22, len(d))
    over = d["actual_hours"] > LIMIT
    ax1.scatter(d.loc[~over, "actual_hours"], y[~over.values], s=16,
                color=GREY, alpha=0.55, edgecolor="none", zorder=2)
    ax1.scatter(d.loc[over, "actual_hours"], y[over.values], s=30,
                color=RED, alpha=0.9, edgecolor="white", lw=0.5, zorder=3)
    m = stats[c]["median"]
    ax1.plot([m, m], [ypos[c] - 0.3, ypos[c] + 0.3], color=DARK, lw=2.2, zorder=4)
    ax1.text(m, ypos[c] + 0.33, f"median {m:.0f} h", ha="center", va="bottom",
             fontsize=8.5, color=DARK)

ax1.set_xlim(0, xmax)
ax1.set_ylim(-0.6, 2.6)
ax1.set_yticks([ypos[c] for c in couriers])
ax1.set_yticklabels([f"{c}\n({stats[c]['n']} deliveries)" for c in couriers], fontsize=10.5)
ax1.set_xlabel("Hours from dispatch to delivery (each dot = one parcel)", fontsize=10)
ax1.set_title("Every delivery, Aug–Oct 2026", fontsize=11, loc="left", color=DARK)

# ---- Right panel: share over 48 h with 95% interval
for c in couriers:
    s = stats[c]
    col = RED if c == "Swiftline" else GREY
    y = ypos[c]
    ax2.barh(y, s["p"] * 100, height=0.5, color=col, alpha=0.9 if c == "Swiftline" else 0.6)
    ax2.errorbar(s["p"] * 100, y,
                 xerr=[[100 * (s["p"] - s["lo"])], [100 * (s["hi"] - s["p"])]],
                 fmt="none", ecolor=DARK, elinewidth=1.2, capsize=4)
    ax2.text(100 * s["hi"] + 1.2, y,
             f"{s['p']*100:.0f}%  ({s['k']} of {s['n']})",
             va="center", ha="left", fontsize=11,
             fontweight="bold" if c == "Swiftline" else "normal",
             color=RED if c == "Swiftline" else DARK)

ax2.set_xlim(0, 45)
ax2.set_xlabel("% of parcels over 48 h\n(line = 95% range of plausible rates)", fontsize=10)
ax2.set_title("Share past the cold-pack limit", fontsize=11, loc="left", color=DARK)
ax2.tick_params(axis="y", left=False)

for ax in (ax1, ax2):
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(labelsize=9.5)

# ---- Headline
costs = [stats[c]["cost"] for c in couriers]
fig.text(0.02, 0.955,
         "Swiftline let 1 in 7 parcels go past the 48-hour cold-pack limit",
         fontsize=16, fontweight="bold", color=DARK, ha="left", va="top")
fig.text(0.02, 0.885,
         f"Northway and ParcelPro: about 2%. Prices differ by under $0.50 "
         f"(${min(costs):.2f}–${max(costs):.2f}) and ratings are alike, so cold-chain reliability should decide.\n"
         "Swiftline is faster on a typical parcel, but its failures are severe. "
         "ParcelPro's rate rests on only 40 deliveries, hence its wider range.",
         fontsize=10, color="#444444", ha="left", va="top", linespacing=1.4)

fig.text(0.02, 0.02, "Source: Medley Pharmacy delivery records, 3 Aug – 30 Oct 2026 (220 deliveries).",
         fontsize=8, color="#777777", ha="left")
