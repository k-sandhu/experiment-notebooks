import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------- Data ----------
df = pd.read_csv("data.csv")
df["cost_total"] = df["acquisition_cost_per_loan_usd"] * df["funded_loans"]

g = df.groupby("channel").agg(
    apps=("applications", "sum"),
    loans=("funded_loans", "sum"),
    value=("funded_value_musd", "sum"),
    cost_total=("cost_total", "sum"),
)
g["cost_per_loan"] = g["cost_total"] / g["loans"]                 # US$ per funded loan
g["cost_per_1000"] = g["cost_total"] / (g["value"] * 1e6) * 1000  # US$ per $1,000 lent
g["avg_loan_k"] = g["value"] / g["loans"] * 1000                  # $ thousands
g["app_share"] = g["apps"] / g["apps"].sum() * 100
g["val_share"] = g["value"] / g["value"].sum() * 100

order = ["Broker", "Branch", "Online", "Partner app"]
g = g.loc[order]

# ---------- Style ----------
ACCENT = "#1f5fa8"
GREY_TXT = "#555555"
greys = {"Branch": "#bdbdbd", "Online": "#d4d4d4", "Partner app": "#e6e6e6"}
colors = {"Broker": ACCENT, **greys}

fig = plt.figure(figsize=(10, 6))
gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1], wspace=0.35,
                      left=0.13, right=0.88, top=0.76, bottom=0.17)
ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])

b_app = g.loc["Broker", "app_share"]
b_val = g.loc["Broker", "val_share"]

fig.text(0.02, 0.965,
         f"Broker costs the most per loan, but brings {b_val:.0f}% of funded value\n"
         f"from just {b_app:.0f}% of applications",
         fontsize=15, fontweight="bold", ha="left", va="top", color="#222222")
fig.text(0.02, 0.855, "Ridgeview Credit Union lending channels, January to September 2026",
         fontsize=10, color=GREY_TXT, ha="left", va="top")

# ---------- Left panel: acquisition cost per funded loan ----------
y = np.arange(len(order))[::-1]
vals = g["cost_per_loan"].values
ax1.barh(y, vals, color=[colors[c] for c in order], height=0.62)
for yi, v, c in zip(y, vals, order):
    ax1.text(v + 25, yi, f"${v:,.0f}", va="center", fontsize=11,
             fontweight="bold" if c == "Broker" else "normal",
             color=ACCENT if c == "Broker" else GREY_TXT)
ax1.set_yticks(y)
ax1.set_yticklabels(order, fontsize=11)
for lbl in ax1.get_yticklabels():
    if lbl.get_text() == "Broker":
        lbl.set_color(ACCENT)
        lbl.set_fontweight("bold")
ax1.set_xlim(0, vals.max() * 1.22)
ax1.set_xlabel("Acquisition cost per funded loan (US$)", fontsize=9.5, color=GREY_TXT)
ax1.set_title("Cost to acquire each funded loan", loc="left", fontsize=11.5,
              color="#222222", pad=10)
for s in ["top", "right", "left"]:
    ax1.spines[s].set_visible(False)
ax1.tick_params(axis="y", length=0)
ax1.tick_params(axis="x", colors=GREY_TXT, labelsize=9)

ax1.text(0, -0.30,
         f"Per $1,000 lent, broker costs ${g.loc['Broker','cost_per_1000']:.0f}, "
         f"less than branch (${g.loc['Branch','cost_per_1000']:.0f})",
         transform=ax1.transAxes, fontsize=10, color=ACCENT, ha="left", va="top")

# ---------- Right panel: share of applications vs funded value ----------
x = [0, 1]
bottoms = np.zeros(2)
for c in order:
    h = np.array([g.loc[c, "app_share"], g.loc[c, "val_share"]])
    ax2.bar(x, h, bottom=bottoms, color=colors[c], width=0.6,
            edgecolor="white", linewidth=1.2)
    if c == "Broker":
        for xi, hi, bi in zip(x, h, bottoms):
            ax2.text(xi, bi + hi / 2, f"{hi:.0f}%", ha="center", va="center",
                     color="white", fontsize=13, fontweight="bold")
    # channel name to the right of the funded-value bar
    ax2.text(1.34, bottoms[1] + h[1] / 2, c, va="center", ha="left", fontsize=10,
             color=ACCENT if c == "Broker" else GREY_TXT,
             fontweight="bold" if c == "Broker" else "normal")
    bottoms += h

ax2.set_xticks(x)
ax2.set_xticklabels(["Applications", "Funded value"], fontsize=10.5)
ax2.set_xlim(-0.45, 1.45)
ax2.set_ylim(0, 100)
ax2.set_yticks([0, 25, 50, 75, 100])
ax2.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
ax2.set_ylabel("Share of nine-month total", fontsize=9.5, color=GREY_TXT)
ax2.set_title("Broker's share of the business", loc="left", fontsize=11.5,
              color="#222222", pad=10)
for s in ["top", "right"]:
    ax2.spines[s].set_visible(False)
ax2.tick_params(colors=GREY_TXT, labelsize=9)
ax2.tick_params(axis="x", length=0, colors="#222222")

others = g.drop("Broker")["avg_loan_k"]
ax2.text(0, -0.17,
         f"Avg broker loan ${g.loc['Broker','avg_loan_k']:.0f}k vs "
         f"${others.min():.0f}k to ${others.max():.0f}k elsewhere",
         transform=ax2.transAxes, fontsize=10, color=ACCENT, ha="left", va="top")

# ---------- Caveat ----------
fig.text(0.02, 0.035,
         "Caveat: broker lending began only in November 2025, so its 2.1% 12-month default rate is a "
         "model projection, not observed.\nThe same applies to the partner app. "
         "The credit risk of these loans is not yet proven.",
         fontsize=9, color="#8a4b00", ha="left", va="bottom")
