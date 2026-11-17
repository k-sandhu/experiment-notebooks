import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

HL, GREY = "#C0392B", "#9AA0A6"
df = pd.read_csv("data.csv")
g = df.groupby("channel")[["applications", "funded_value_musd"]].sum()
share = pd.DataFrame({"apps": 100 * g.applications / g.applications.sum(),
                      "value": 100 * g.funded_value_musd / g.funded_value_musd.sum()})
acq = df.groupby("channel").acquisition_cost_per_loan_usd.mean()
order = ["Broker", "Branch", "Online", "Partner app"]
y = np.arange(len(order))
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(y - 0.18, share.loc[order, "apps"], height=0.34, color="#D5D8DC")
ax.barh(y + 0.18, share.loc[order, "value"], height=0.34, color=[HL, GREY, GREY, GREY])
ax.text(share.loc["Broker", "apps"] + 0.5, -0.18, f"{share.loc['Broker', 'apps']:.0f}% of applications", va="center", color="#555")
ax.text(share.loc["Broker", "value"] + 0.5, 0.18, f"{share.loc['Broker', 'value']:.0f}% of loan value", va="center", color=HL, fontweight="bold")
ax.set_yticks(y, [f"{c}\n${acq[c]:,.0f} per loan" for c in order])
ax.invert_yaxis()
ax.set_xlim(0, 55)
ax.set_xlabel("Share of Jan-Sep 2026 total, % (light = applications, dark = funded value)")
ax.set_title("Broker costs the most per loan but brings a third of all loan value", fontsize=15, loc="left", pad=28)
ax.text(0, 1.02, "Cost to acquire each funded loan is shown under each channel. Broker and partner-app default rates are "
        "projections (loans too new).", transform=ax.transAxes, fontsize=10.5, color="#333")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", alpha=0.25)
fig.tight_layout()
