import pandas as pd
import matplotlib.pyplot as plt

HL, GREY = "#C0392B", "#9AA0A6"
df = pd.read_csv("data.csv")
urg = df[df.triage_category == "Urgent"].set_index("hospital").median_wait_min.sort_values()
lw = df.assign(n=df.visits * df.left_without_being_seen_pct / 100).groupby("hospital")[["n", "visits"]].sum()
lwbs = 100 * lw.n / lw.visits
names = list(urg.index)
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(names, urg.values, color=[HL if h == "Riverside" else GREY for h in names])
bars[names.index("Northgate")].set_facecolor("#D5D8DC")
bars[names.index("Northgate")].set_hatch("///")
ax.text(urg["Riverside"] + 1, names.index("Riverside"), f"{urg['Riverside']} min", va="center", color=HL, fontweight="bold")
ax.text(urg["Northgate"] + 1, names.index("Northgate"), "clock starts at registration,\nabout 26 min on the same basis",
        va="center", fontsize=9.5, color="#333")
ax.set_title("Urgent patients wait twice as long at Riverside", fontsize=15, loc="left", pad=28)
ax.text(0, 1.02, f"Median minutes to see a doctor, urgent patients, Jul-Sep 2026. {lwbs['Riverside']:.1f}% of Riverside patients "
        f"left without being seen (others: {lwbs.drop('Riverside').mean():.1f}%).", transform=ax.transAxes, fontsize=10.5, color="#333")
ax.set_xlabel("Median wait for urgent patients, minutes")
ax.set_xlim(0, 80)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", alpha=0.25)
fig.tight_layout()
