import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Read data
df = pd.read_csv("data.csv", parse_dates=["date"])

variant_order = ["control", "new_checkout"]
labels = {"control": "Control (old)", "new_checkout": "New checkout"}
colors = {"control": "#4C72B0", "new_checkout": "#DD8452"}

# Aggregate conversion by device and variant
agg = (
    df.groupby(["variant", "device"], as_index=False)
      .agg(sessions=("sessions", "sum"), orders=("orders", "sum"))
)
agg["conversion_pct"] = agg["orders"] / agg["sessions"] * 100

# Daily overall conversion
daily_overall = (
    df.groupby(["date", "variant"], as_index=False)
      .agg(sessions=("sessions", "sum"), orders=("orders", "sum"))
)
daily_overall["conversion_pct"] = (
    daily_overall["orders"] / daily_overall["sessions"] * 100
)

# Daily mobile conversion
mobile = df[df["device"] == "mobile"]
daily_mobile = (
    mobile.groupby(["date", "variant"], as_index=False)
          .agg(sessions=("sessions", "sum"), orders=("orders", "sum"))
)
daily_mobile["conversion_pct"] = (
    daily_mobile["orders"] / daily_mobile["sessions"] * 100
)

# Daily desktop conversion
desktop = df[df["device"] == "desktop"]
daily_desktop = (
    desktop.groupby(["date", "variant"], as_index=False)
           .agg(sessions=("sessions", "sum"), orders=("orders", "sum"))
)
daily_desktop["conversion_pct"] = (
    daily_desktop["orders"] / daily_desktop["sessions"] * 100
)

fig, axes = plt.subplots(2, 2, figsize=(10, 6))

# Panel 1: Aggregate conversion by device
devices = ["desktop", "mobile", "tablet"]
x = np.arange(len(devices))
width = 0.36

for i, variant in enumerate(variant_order):
    vals = []
    for device in devices:
        row = agg[(agg["variant"] == variant) & (agg["device"] == device)]
        vals.append(row["conversion_pct"].iloc[0] if len(row) else np.nan)

    axes[0, 0].bar(
        x + (i - 0.5) * width,
        vals,
        width,
        label=labels[variant],
        color=colors[variant],
    )

    for xi, val in zip(x + (i - 0.5) * width, vals):
        if not np.isnan(val):
            axes[0, 0].text(
                xi, val + 0.04, f"{val:.2f}",
                ha="center", va="bottom", fontsize=7
            )

axes[0, 0].set_xticks(x)
axes[0, 0].set_xticklabels([d.capitalize() for d in devices])
axes[0, 0].set_ylabel("Conversion (%)")
axes[0, 0].set_title("Conversion by device (14-day totals)")
axes[0, 0].legend(frameon=False)
axes[0, 0].grid(axis="y", alpha=0.25)
axes[0, 0].set_ylim(bottom=0)

# Panel 2: Mobile conversion over time
for variant in variant_order:
    sub = daily_mobile[daily_mobile["variant"] == variant].sort_values("date")
    axes[0, 1].plot(
        sub["date"], sub["conversion_pct"],
        marker="o", markersize=3, linewidth=1.5,
        color=colors[variant], label=labels[variant]
    )

axes[0, 1].axvline(
    pd.Timestamp("2026-09-26"),
    color="black", linestyle="--", linewidth=1, alpha=0.7
)
axes[0, 1].text(
    pd.Timestamp("2026-09-26"), 0.95, " bug fixed",
    transform=axes[0, 1].get_xaxis_transform(),
    fontsize=7, va="top"
)
axes[0, 1].axvspan(
    pd.Timestamp("2026-09-20"), pd.Timestamp("2026-09-21"),
    color="gray", alpha=0.12, linewidth=0
)
axes[0, 1].xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
axes[0, 1].tick_params(axis="x", rotation=45)
axes[0, 1].set_ylabel("Conversion (%)")
axes[0, 1].set_title("Mobile conversion over time")
axes[0, 1].legend(frameon=False, fontsize=8)
axes[0, 1].grid(alpha=0.25)

# Panel 3: Desktop conversion over time
for variant in variant_order:
    sub = daily_desktop[daily_desktop["variant"] == variant].sort_values("date")
    axes[1, 0].plot(
        sub["date"], sub["conversion_pct"],
        marker="o", markersize=3, linewidth=1.5,
        color=colors[variant], label=labels[variant]
    )

axes[1, 0].axvline(
    pd.Timestamp("2026-09-26"),
    color="black", linestyle="--", linewidth=1, alpha=0.7
)
axes[1, 0].axvspan(
    pd.Timestamp("2026-09-20"), pd.Timestamp("2026-09-21"),
    color="gray", alpha=0.12, linewidth=0
)
axes[1, 0].xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
axes[1, 0].tick_params(axis="x", rotation=45)
axes[1, 0].set_ylabel("Conversion (%)")
axes[1, 0].set_title("Desktop conversion over time")
axes[1, 0].legend(frameon=False, fontsize=8)
axes[1, 0].grid(alpha=0.25)

# Panel 4: Daily total orders by variant
for variant in variant_order:
    sub = daily_overall[daily_overall["variant"] == variant].sort_values("date")
    axes[1, 1].plot(
        sub["date"], sub["orders"],
        marker="o", markersize=3, linewidth=1.5,
        color=colors[variant], label=labels[variant]
    )

axes[1, 1].axvline(
    pd.Timestamp("2026-09-26"),
    color="black", linestyle="--", linewidth=1, alpha=0.7
)
axes[1, 1].axvspan(
    pd.Timestamp("2026-09-20"), pd.Timestamp("2026-09-21"),
    color="gray", alpha=0.12, linewidth=0
)
axes[1, 1].xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
axes[1, 1].tick_params(axis="x", rotation=45)
axes[1, 1].set_ylabel("Orders")
axes[1, 1].set_title("Daily orders")
axes[1, 1].legend(frameon=False, fontsize=8)
axes[1, 1].grid(alpha=0.25)

fig.suptitle("Checkout experiment: conversion and orders", fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.95])
