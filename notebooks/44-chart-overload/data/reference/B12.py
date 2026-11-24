import pandas as pd
import matplotlib.pyplot as plt

HL, GREY = "#C0392B", "#9AA0A6"
df = pd.read_csv("data.csv")
pre = df[df.month < "2026-06"].groupby("district").litres_per_household_day.mean()
post = df[df.month >= "2026-06"].groupby("district").litres_per_household_day.mean()
cut = (100 * (1 - post / pre)).sort_values()
tgt = df.groupby("district").target_lphd.first()
names = list(cut.index)
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(names, cut.values, color=[HL if d == "Hillcrest" else GREY for d in names])
ax.axvline(20, color="#333", ls="--", lw=1.2)
ax.text(20.3, 7.35, "20% target", fontsize=10)
i = names.index("Hillcrest")
ax.text(cut["Hillcrest"] + 0.4, i, f"{cut['Hillcrest']:.0f}%: {post['Hillcrest']:.0f} L/day vs {tgt['Hillcrest']} L target\n"
        "new meters (July) read about 8% high; true cut about 9%", va="center", color=HL, fontsize=10)
ax.set_xlabel("Cut in use per household, Jun-Sep vs Apr-May 2026, %")
ax.set_xlim(0, 30)
ax.set_title(f"Hillcrest cut water use by only {cut['Hillcrest']:.0f}%; the other districts cut "
             f"{cut.drop('Hillcrest').min():.0f}-{cut.max():.0f}%", fontsize=14.5, loc="left", pad=12)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", alpha=0.25)
fig.tight_layout()
