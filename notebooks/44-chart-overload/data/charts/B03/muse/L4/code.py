import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv", parse_dates=["date"])

# Aggregate conversion over the whole test, by device and variant
agg = df.groupby(["device", "variant"], as_index=False)[["sessions", "orders"]].sum()
agg["conversion"] = 100 * agg["orders"] / agg["sessions"]
conv = agg.pivot(index="device", columns="variant", values="conversion")

sessions_by_device = df.groupby("device")["sessions"].sum()
mobile_share = sessions_by_device["mobile"] / sessions_by_device.sum()
desktop_share = sessions_by_device["desktop"] / sessions_by_device.sum()
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
fig.subplots_adjust(left=0.08, right=0.97, top=0.74, bottom=0.19)

# Title states the decision; subtitle gives the overall consequence
fig.text(
    0.07, 0.97,
    "Do not roll out the new checkout to all yet:\n"
    "the mobile drop wipes out the desktop gain",
    fontsize=19, fontweight="bold", ha="left", va="top", color="#111111",
)
fig.text(
    0.07, 0.835,
    f"Mobile is {mobile_share:.0%} of sessions, so overall the new checkout "
    f"made {abs(orders_change_pct):.1f}% fewer orders "
    f"({orders_by_variant['new_checkout']:,} vs {orders_by_variant['control']:,}).",
    fontsize=11.5, ha="left", va="top", color="#333333",
)

# Wider separation between groups leaves room for the post-fix annotation
x = np.array([0.0, 1.6])
w = 0.42
old_vals = [mobile_old, desktop_old]
new_vals = [mobile_new, desktop_new]

ax.bar(x - w / 2, old_vals, width=w, color="#BDBDBD")
ax.bar(x + w / 2, new_vals, width=w, color=["#C1272D", "#7A7A7A"])

# Consistent direct labels on every bar; variants need no legend
ax.text(x[0] - w / 2, mobile_old + 0.08, f"Old\n{mobile_old:.2f}%",
        ha="center", va="bottom", fontsize=10.5, color="#444444", linespacing=1.15)
ax.text(x[0] + w / 2, mobile_new + 0.08, f"New\n{mobile_new:.2f}%",
        ha="center", va="bottom", fontsize=10.5, fontweight="bold",
        color="#C1272D", linespacing=1.15)
ax.text(x[1] - w / 2, desktop_old + 0.08, f"Old\n{desktop_old:.2f}%",
        ha="center", va="bottom", fontsize=10.5, color="#444444", linespacing=1.15)
ax.text(x[1] + w / 2, desktop_new + 0.08, f"New\n{desktop_new:.2f}%",
        ha="center", va="bottom", fontsize=10.5, color="#444444", linespacing=1.15)

# The change in each group is the message: give both, emphasise mobile
ax.text(
    x[0], mobile_old + 0.78,
    f"{mobile_new - mobile_old:+.2f} pp",
    ha="center", va="center", fontsize=11, fontweight="bold", color="#C1272D",
    bbox=dict(boxstyle="round,pad=0.35", facecolor="#FDECEC", edgecolor="none"),
)
ax.text(
    x[1], desktop_new + 0.62,
    f"{desktop_new - desktop_old:+.2f} pp",
    ha="center", va="center", fontsize=11, color="#444444",
    bbox=dict(boxstyle="round,pad=0.35", facecolor="#EEEEEE", edgecolor="none"),
)

# Caveat shown where it applies: post-fix level as a dashed marker on the red bar
mobile_new_x = x[0] + w / 2
ax.hlines(
    post_fix_conv,
    mobile_new_x - w / 2 - 0.04, mobile_new_x + w / 2 + 0.10,
    colors="#111111", linestyles="--", linewidth=1.6,
)
ax.annotate(
    "", xy=(mobile_new_x + w / 2 + 0.10, post_fix_conv),
    xytext=(mobile_new_x + w / 2 + 0.22, post_fix_conv),
    arrowprops=dict(arrowstyle="-", color="#111111", linewidth=1.0),
)
ax.text(
    mobile_new_x + w / 2 + 0.26, post_fix_conv,
    f"After 26 Sep bug fix:\n{post_fix_conv:.2f}% (only 2 days)",
    ha="left", va="center", fontsize=9.5, color="#222222", linespacing=1.25,
)

ax.set_xticks(x)
ax.set_xticklabels(
    [f"Mobile\n{mobile_share:.0%} of sessions",
     f"Desktop\n{desktop_share:.0%} of sessions"],
    fontsize=11.5,
)
ax.set_xlim(-0.62, 2.22)
ax.set_ylim(0, 4.6)
ax.set_yticks([0, 1, 2, 3, 4])
ax.set_yticklabels(["0%", "1%", "2%", "3%", "4%"], fontsize=10)
ax.set_ylabel("Conversion (orders as % of sessions)", fontsize=11)
ax.yaxis.grid(True, color="#DDDDDD", linewidth=0.8)
ax.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)
ax.spines["bottom"].set_color("#888888")
ax.tick_params(axis="y", length=0)
ax.tick_params(axis="x", length=0)

# Short footer: scope only; the bug-fix caveat is already annotated on the bars
fig.text(
    0.07, 0.035,
    f"14-27 Sep. Tablets excluded ({tablet_share:.0%} of sessions). "
    "Two post-fix days are too short to judge - keep the test running.",
    fontsize=9.5, ha="left", va="bottom", color="#555555",
)
