import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Urgent-patient median wait per hospital
urgent = df[df["triage_category"] == "Urgent"].set_index("hospital")["median_wait_min"]

# Visit-weighted share of patients leaving without being seen, all triage categories
df["lwbs_n"] = df["visits"] * df["left_without_being_seen_pct"] / 100
g = df.groupby("hospital")[["lwbs_n", "visits"]].sum()
lwbs = 100 * g["lwbs_n"] / g["visits"]

order = urgent.sort_values(ascending=False).index.tolist()
urgent = urgent.reindex(order)
lwbs = lwbs.reindex(order)

focus = "Riverside"
HL, GREY, LIGHT, DARK = "#c0392b", "#c8c8c8", "#ececec", "#555555"
colors = [HL if h == focus else GREY for h in order]
y = np.arange(len(order))

others_wait = urgent.drop(focus).mean()
others_lwbs = 100 * g.drop(focus)["lwbs_n"].sum() / g.drop(focus)["visits"].sum()

# Northgate measures from registration (~15 min earlier than triage)
NG_OFFSET = 15
ng_adj = urgent["Northgate"] - NG_OFFSET

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6), sharey=True)

# Panel 1: urgent median wait
plot_wait = urgent.copy()
plot_wait["Northgate"] = ng_adj
ax1.barh(y, plot_wait.values, color=colors, height=0.65)
ng = order.index("Northgate")
ax1.barh(ng, NG_OFFSET, left=ng_adj, color=LIGHT, height=0.65,
         edgecolor=GREY, linewidth=0.8, linestyle=(0, (2, 2)))
ax1.text(urgent["Northgate"] + 1.5, ng,
         "≈15 min is registration time,\nnot counted at other hospitals",
         va="center", fontsize=8, color=DARK, style="italic")

ax1.axvline(others_wait, color=DARK, lw=1, ls="--")
ax1.text(others_wait + 1, len(order) - 0.45, f"Other 7 avg: {others_wait:.0f} min",
         color=DARK, fontsize=9, va="bottom")
ax1.text(urgent[focus] + 1.5, 0, f"{urgent[focus]:.0f} min", va="center",
         color=HL, fontsize=12, fontweight="bold")
ax1.set_title("Median wait to see a doctor,\nurgent patients (minutes)",
              fontsize=11, loc="left", color="#333333")
ax1.set_xlim(0, 75)

# Panel 2: left without being seen
ax2.barh(y, lwbs.values, color=colors, height=0.65)
ax2.axvline(others_lwbs, color=DARK, lw=1, ls="--")
ax2.text(others_lwbs + 0.15, len(order) - 0.45, f"Other 7 avg: {others_lwbs:.1f}%",
         color=DARK, fontsize=9, va="bottom")
ax2.text(lwbs[focus] + 0.2, 0, f"{lwbs[focus]:.1f}%", va="center",
         color=HL, fontsize=12, fontweight="bold")
ax2.set_title("Patients who left without being seen,\nall visits (%)",
              fontsize=11, loc="left", color="#333333")
ax2.set_xlim(0, 11.5)

ax1.set_yticks(y)
ax1.set_yticklabels(order, fontsize=11)
for lbl in ax1.get_yticklabels():
    if lbl.get_text() == focus:
        lbl.set_color(HL)
        lbl.set_fontweight("bold")
ax1.invert_yaxis()

for ax in (ax1, ax2):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", colors=DARK, labelsize=9)

fig.suptitle("Riverside should get the 12 triage nurses: its urgent patients wait twice as long,\n"
             "and nearly 3 times as many patients leave without being seen",
             fontsize=14, fontweight="bold", x=0.02, ha="left", y=0.97)
fig.text(0.02, 0.02,
         "Lakeshore Health emergency departments, July–September 2026. Wait = arrival to first seen by a doctor, "
         "clock starts at triage (Northgate: at registration). Average includes Northgate's reported 41 min.",
         fontsize=7.5, color=DARK, ha="left")

fig.subplots_adjust(left=0.11, right=0.97, top=0.78, bottom=0.11, wspace=0.3)
