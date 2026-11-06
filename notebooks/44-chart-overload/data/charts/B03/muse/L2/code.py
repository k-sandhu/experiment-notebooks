import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv", parse_dates=["date"])

# Aggregate conversion over the whole test, by device and variant
agg = (
    df.groupby(["device", "variant"], as_index=False)[["sessions", "orders"]]
    .sum()
)
agg["conversion"] = 100 * agg["orders"] / agg["sessions"]
conv = agg.pivot(index="device", columns="variant", values="conversion")

sessions_by_device = df.groupby("device")["sessions"].sum()
mobile_share = sessions_by_device["mobile"] / sessions_by_device.sum()
tablet_share = sessions_by_device["tablet"] / sessions_by_device.sum()

orders_by_variant = df.groupby("variant")["orders"].sum()
orders_change_pct = (
    100
    * (orders_by_variant["new_checkout"] - orders_by_variant["control"])
    / orders_by_variant["control"]
)

# Mobile conversion on the new checkout after the 26 Sep bug fix
post_fix = df[
    (df["date"] >= "2026-09-26")
    & (df["variant"] == "new_checkout")
    & (df["device"] == "mobile")
]
post_fix_conv = 100 * post_fix["orders"].sum() / post_fix["sessions"].sum()

mobile_old = conv.loc["mobile", "control"]
mobile_new = conv.loc["mobile", "new_checkout"]
desktop_old = conv.loc["desktop", "control"]
desktop_new = conv.loc["desktop", "new_checkout"]

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(left=0.09, right=0.96, top=0.76, bottom=0.21)

# Title states the decision message
fig.text(
    0.07, 0.97,
    "Do not roll out the new checkout to all yet:\n"
    "the mobile drop wipes out the desktop gain",
    fontsize=19, fontweight="bold", ha="left", va="top", color="#111111",
)
fig.text(
    0.07, 0.845,
    f"Mobile is {mobile_share:.0%} of sessions, so overall the new checkout "
    f"made {abs(orders_change_pct):.1f}% fewer orders "
    f"({orders_by_variant['new_checkout']:,} vs {orders_by_variant['control']:,}).",
    fontsize=11.5, ha="left", va="top", color="#333333",
)

# Bars: tablets excluded (only ~3% of sessions); one strong colour for the problem
x = np.array([0, 1])
w = 0.34
old_vals = [mobile_old, desktop_old]
new_vals = [mobile_new, desktop_new]

ax.bar(x - w / 2, old_vals, width=w, color="#BFBFBF")
ax.bar(x + w / 2, new_vals, width=w, color=["#C1272D", "#6E6E6E"])

# Direct labels instead of a legend; numbers only for the mobile message
ax.text(x[0] - w / 2, mobile_old + 0.09, f"Old checkout\n{mobile_old:.2f}%",
        ha="center", va="bottom", fontsize=11, color="#444444")
ax.text(x[0] + w / 2, mobile_new + 0.09, f"New checkout\n{mobile_new:.2f}%",
        ha="center", va="bottom", fontsize=11, fontweight="bold", color="#C1272D")
ax.text(x[1] - w / 2, desktop_old + 0.09, "Old",
        ha="center", va="bottom", fontsize=10, color="#666666")
ax.text(x[1] + w / 2, desktop_new + 0.09, "New",
        ha="center", va="bottom", fontsize=10, color="#666666")
ax.text(x[1], max(desktop_old, desktop_new) + 0.55,
        f"+{desktop_new - desktop_old:.2f} pp on desktop",
        ha="center", va="bottom", fontsize=10.5, color="#444444")

ax.set_xticks(x)
ax.set_xticklabels(
    [f"Mobile\n{mobile_share:.0%} of sessions", "Desktop"],
    fontsize=12,
)
ax.set_ylim(0, 4.6)
ax.set_yticks([0, 1, 2, 3, 4])
ax.set_yticklabels(["0%", "1%", "2%", "3%", "4%"])
ax.set_ylabel("Conversion (orders as % of sessions)", fontsize=11)
ax.yaxis.grid(True, color="#DDDDDD", linewidth=0.8)
ax.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)
ax.spines["bottom"].set_color("#888888")
ax.tick_params(axis="y", length=0)

# Caveat that changes how the chart should be read
fig.text(
    0.07, 0.045,
    f"Caveat: a bug hiding the payment button on some phones in the new checkout was fixed on 26 Sep.\n"
    f"New mobile conversion was {post_fix_conv:.2f}% on 26-27 Sep, close to the old checkout, but two days "
    f"is too short to judge - keep the test running.\n"
    f"14-27 Sep. Tablets excluded ({tablet_share:.0%} of sessions).",
    fontsize=9.5, ha="left", va="bottom", color="#555555",
)
