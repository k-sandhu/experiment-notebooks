import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

HL, GREY = "#C0392B", "#9AA0A6"
df = pd.read_csv("data.csv")
g = df.groupby(["device", "variant"])[["orders", "sessions"]].sum()
rate = (100 * g.orders / g.sessions).unstack()
tot = df.groupby("variant").orders.sum()
change = (tot["new_checkout"] / tot["control"] - 1) * 100
devs = ["mobile", "desktop"]
y = np.arange(len(devs))
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(y + 0.18, rate.loc[devs, "control"], height=0.34, color=GREY)
ax.barh(y - 0.18, rate.loc[devs, "new_checkout"], height=0.34, color=[HL, "#5D6D7E"])
for i, d in enumerate(devs):
    ax.text(rate.loc[d, "control"] + 0.05, i + 0.18, f"Old {rate.loc[d, 'control']:.2f}%", va="center", color="#555")
    ax.text(rate.loc[d, "new_checkout"] + 0.05, i - 0.18, f"New {rate.loc[d, 'new_checkout']:.2f}%", va="center",
            color=HL if d == "mobile" else "#333", fontweight="bold" if d == "mobile" else "normal")
ax.set_yticks(y, ["Mobile\n(68% of sessions)", "Desktop\n(29%)"])
ax.invert_yaxis()
ax.set_xlim(0, 4.6)
ax.set_xlabel("Conversion: orders as % of sessions, 14-27 Sep 2026")
ax.set_title(f"The new checkout lowers mobile conversion, so total orders fell {abs(change):.1f}%", fontsize=14.5, loc="left", pad=12)
ax.text(0, -0.17, "Caveat: a bug hiding the payment button on some phones was fixed on 26 Sep. Mobile looked closer to the old\n"
        "checkout on 26-27 Sep, but two days is too short to judge.", transform=ax.transAxes, fontsize=10, color="#333", va="top")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", alpha=0.25)
fig.tight_layout()
