import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("data.csv", parse_dates=["month"])
df = df.sort_values(["plan", "month"])

# September 2026 is only 1-14 Sep: its cancellation rate would look
# artificially low, so end the chart at August.
df = df[df["month"] <= "2026-08-01"]

family = df[df["plan"] == "Family"]
others = df[df["plan"] != "Family"]

pre = family[family["month"] < "2026-04-01"]["cancellation_rate_pct"].mean()
post = family[family["month"] >= "2026-04-01"]["cancellation_rate_pct"].mean()

RED = "#B42318"
GREY = "#A8A8A8"
DARK_GREY = "#666666"

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(left=0.09, right=0.98, top=0.82, bottom=0.15)

# The price rise sits between the March and April points.
rise_boundary = pd.Timestamp("2026-03-16")

# Context first: the three plans whose prices did not change.
# Final values in Aug are Couple 3.06, Vegetarian 2.60, Single 2.43 --
# too close to label at their true heights, so spread the labels
# vertically while keeping their top-to-bottom order.
label_y = {"Couple": 3.30, "Vegetarian": 2.78, "Single": 2.26}
label_x = pd.Timestamp("2026-08-01") + pd.Timedelta(days=8)

for plan, g in others.groupby("plan"):
    ax.plot(g["month"], g["cancellation_rate_pct"],
            color=GREY, linewidth=1.6, marker="o", markersize=3.5, zorder=2)
    last = g.iloc[-1]
    # Short leader from the last point to its displaced label.
    ax.plot([last["month"], label_x - pd.Timedelta(days=2)],
            [last["cancellation_rate_pct"], label_y[plan]],
            color=GREY, linewidth=0.8, zorder=1)
    ax.text(label_x, label_y[plan], plan,
            color=DARK_GREY, fontsize=10, va="center")

# The plan that matters for this decision.
ax.plot(family["month"], family["cancellation_rate_pct"],
        color=RED, linewidth=3.5, marker="o", markersize=6, zorder=3)
last_f = family.iloc[-1]
ax.text(label_x, last_f["cancellation_rate_pct"],
        "Family", color=RED, fontsize=12, fontweight="bold", va="center")

# The intervention.
ax.axvline(rise_boundary, color=DARK_GREY, linewidth=1.2,
           linestyle="--", zorder=1)
ax.text(rise_boundary - pd.Timedelta(days=6), 7.75,
        "1 April: Family price\n\\$79 \u2192 \\$89 per week",
        color=DARK_GREY, fontsize=10.5, ha="right", va="top")

# Only the two numbers that carry the message.
ax.text(pd.Timestamp("2026-01-01"), 3.90,
        f"Before: {pre:.1f}% a month",
        color=RED, fontsize=11.5, fontweight="bold", ha="center")
ax.text(pd.Timestamp("2026-06-10"), 7.30,
        f"Apr\u2013Aug: {post:.1f}% a month",
        color=RED, fontsize=11.5, fontweight="bold", ha="center")

ax.set_title("Family cancellations doubled after the April price rise\n"
             "and stayed high \u2014 other plans did not change",
             loc="left", fontsize=16, fontweight="bold", pad=16)
ax.set_ylabel("Cancellations (% of active subscribers per month)", fontsize=11)
ax.set_xlabel("")

ax.set_ylim(0, 8)
ax.set_yticks([0, 2, 4, 6, 8])
ax.set_yticklabels(["0%", "2%", "4%", "6%", "8%"])

# Show only months with data (Oct-Aug); extend xlim just far enough
# for the direct labels, with no empty September tick.
months = pd.date_range("2025-10-01", "2026-08-01", freq="MS")
ax.set_xlim(pd.Timestamp("2025-09-26"), pd.Timestamp("2026-09-07"))
ax.set_xticks(months)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
ax.tick_params(axis="x", labelsize=9.5)
ax.tick_params(axis="y", labelsize=10)
ax.grid(axis="y", color="#DDDDDD", linewidth=0.8)
ax.set_axisbelow(True)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

fig.text(0.09, 0.02,
         "September 2026 excluded: it covers 1\u201314 Sep only, so its rate would understate cancellations. "
         "Other plans' prices were unchanged.",
         fontsize=8.5, color=DARK_GREY)
