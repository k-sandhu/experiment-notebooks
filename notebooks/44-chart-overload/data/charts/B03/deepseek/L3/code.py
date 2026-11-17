import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Read data
df = pd.read_csv("data.csv")
df["date"] = pd.to_datetime(df["date"])

# Aggregate conversion for mobile and desktop
devices = ["mobile", "desktop"]
agg = (
    df[df["device"].isin(devices)]
    .groupby(["device", "variant"])
    .agg(sessions=("sessions", "sum"), orders=("orders", "sum"))
    .reset_index()
)
agg["conversion_pct"] = agg["orders"] / agg["sessions"] * 100
conv = agg.pivot(index="device", columns="variant", values="conversion_pct").loc[devices]

# Overall totals and shares
totals = df.groupby("variant")["orders"].sum()
old_total = totals["control"]
new_total = totals["new_checkout"]
pct_change = (new_total - old_total) / old_total * 100
mobile_share = (
    df.groupby("device")["sessions"].sum()["mobile"] / df["sessions"].sum() * 100
)

# Post-fix mobile conversion for new checkout
post_fix = df[
    (df["date"] >= "2026-09-26")
    & (df["variant"] == "new_checkout")
    & (df["device"] == "mobile")
]
post_fix_conv = post_fix["orders"].sum() / post_fix["sessions"].sum() * 100

# Plot
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(devices))
width = 0.34
old_vals = conv["control"].values
new_vals = conv["new_checkout"].values

ax.bar(
    x - width / 2,
    old_vals,
    width,
    color="#bdbdbd",
    edgecolor="white",
    label="Old checkout",
)
ax.bar(
    x + width / 2,
    new_vals,
    width,
    color="#c0392b",
    edgecolor="white",
    label="New checkout",
)

# Direct labels on bars
for i, v in enumerate(old_vals):
    ax.text(
        x[i] - width / 2,
        v + 0.07,
        f"old\n{v:.2f}%",
        ha="center",
        va="bottom",
        fontsize=10,
        color="#555555",
    )
for i, v in enumerate(new_vals):
    ax.text(
        x[i] + width / 2,
        v + 0.07,
        f"new\n{v:.2f}%",
        ha="center",
        va="bottom",
        fontsize=10,
        color="#c0392b",
        fontweight="bold",
    )

ax.set_xticks(x)
ax.set_xticklabels(
    [f"Mobile\n({mobile_share:.0f}% of sessions)", "Desktop"],
    fontsize=12,
)
ax.set_ylabel("Conversion rate (%)", fontsize=11)
ax.set_ylim(0, 4.3)
ax.set_yticks(np.arange(0, 5, 1))
ax.grid(axis="y", color="#e5e5e5", linewidth=0.8)
ax.set_axisbelow(True)

for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.spines["left"].set_color("#cccccc")
ax.spines["bottom"].set_color("#cccccc")
ax.tick_params(colors="#333333")

# Title and subtitle
fig.text(
    0.01,
    0.95,
    f"New checkout cut total orders by {abs(pct_change):.1f}%: mobile decline outweighed desktop gain",
    ha="left",
    va="top",
    fontsize=15,
    fontweight="bold",
    color="#222222",
)
fig.text(
    0.01,
    0.895,
    f"Total orders over 14 days: {old_total:,} old vs {new_total:,} new. Mobile is {mobile_share:.0f}% of sessions.",
    ha="left",
    va="top",
    fontsize=11,
    color="#444444",
)

# Caveat
fig.text(
    0.01,
    0.035,
    f"Caveat: payment-button bug on some phones fixed 26 Sep. New mobile conversion was {post_fix_conv:.2f}% on 26–27 Sep, but two days is too short to judge.",
    ha="left",
    va="bottom",
    fontsize=9,
    color="#666666",
)

fig.subplots_adjust(left=0.09, right=0.98, top=0.80, bottom=0.14)
