import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# Load data
df = pd.read_csv("data.csv")
df["signup_month"] = pd.to_datetime(df["signup_month"] + "-01")
df = df.sort_values(["signup_month", "day"])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6))

# Left panel: retention curves by cohort, colored by onboarding version
colors = {"old": "tab:blue", "new": "tab:orange"}

for month, g in df.groupby("signup_month"):
    version = g["onboarding_version"].iloc[0]
    linestyle = "--" if month == pd.Timestamp("2026-09-01") else "-"
    ax1.plot(
        g["day"],
        g["retention_pct"],
        color=colors.get(version, "gray"),
        linestyle=linestyle,
        marker="o",
        markersize=2.5,
        linewidth=1.1,
        alpha=0.35,
    )

for version in ["old", "new"]:
    sub = df[df["onboarding_version"] == version]
    avg = sub.groupby("day")["retention_pct"].mean().sort_index()
    ax1.plot(
        avg.index,
        avg.values,
        color=colors[version],
        linewidth=3,
        label=f"{version.capitalize()} onboarding (mean)",
    )

ax1.set_title("Retention by cohort")
ax1.set_xlabel("Days since sign-up")
ax1.set_ylabel("Retention (%)")
ax1.set_xticks([1, 7, 14, 30, 60, 90])
ax1.grid(alpha=0.25)
ax1.legend(loc="upper right")

# Right panel: day-30 retention by cohort and 30-day paid conversion
day30 = df[df["day"] == 30].sort_values("signup_month").copy()
x = np.arange(len(day30))
bar_colors = day30["onboarding_version"].map(colors)

ax2.bar(
    x,
    day30["retention_pct"],
    color=bar_colors,
    alpha=0.7,
    label="Day-30 retention",
)
ax2.set_ylabel("Day-30 retention (%)")
ax2.set_xlabel("Signup month (2026)")
ax2.set_title("Day-30 retention and paid conversion by cohort")
ax2.set_xticks(x)
ax2.set_xticklabels(day30["signup_month"].dt.strftime("%b"))
ax2.grid(axis="y", alpha=0.25)

ax2b = ax2.twinx()
ax2b.plot(
    x,
    day30["paid_conversion_30d_pct"],
    color="black",
    marker="o",
    linewidth=1.5,
    label="Paid conversion 30d",
)
ax2b.set_ylabel("Paid conversion 30d (%)")

# Shade the TV-campaign period (Jun-Aug) on the right panel
month_labels = day30["signup_month"].dt.strftime("%Y-%m").to_list()
has_campaign = "2026-06" in month_labels and "2026-08" in month_labels
if has_campaign:
    start = month_labels.index("2026-06") - 0.5
    end = month_labels.index("2026-08") + 0.5
    ax2.axvspan(start, end, color="gray", alpha=0.12)

handles = [
    Patch(color=colors["old"], alpha=0.7, label="Old onboarding"),
    Patch(color=colors["new"], alpha=0.7, label="New onboarding"),
    plt.Line2D([0], [0], color="black", marker="o", linewidth=1.5,
               label="Paid conversion 30d"),
]
if has_campaign:
    handles.append(Patch(color="gray", alpha=0.12, label="TV campaign"))

ax2.legend(handles=handles, loc="upper left", fontsize=8)

fig.tight_layout()
