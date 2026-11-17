import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("data.csv", parse_dates=["date"]).sort_values("date")
df["capacity_plus_40"] = df["available_capacity_mw"] + 40
df["shortfall_now"] = df["actual_peak_mw"] - df["available_capacity_mw"]
df["shortfall_after_40"] = df["actual_peak_mw"] - df["capacity_plus_40"]

fig, ax = plt.subplots(figsize=(10, 6))

ax.axvspan(
    pd.Timestamp("2026-01-10"),
    pd.Timestamp("2026-01-17"),
    color="0.85",
    alpha=0.55,
    label="Unit 3 outage (10–16 Jan)",
    zorder=0,
)

ax.plot(
    df["date"],
    df["actual_peak_mw"],
    color="black",
    lw=2.2,
    marker="o",
    ms=2,
    label="Actual peak demand",
    zorder=4,
)
ax.plot(
    df["date"],
    df["available_capacity_mw"],
    color="#1f77b4",
    lw=2,
    label="Available capacity",
    zorder=3,
)
ax.plot(
    df["date"],
    df["capacity_plus_40"],
    color="#2ca02c",
    lw=2,
    ls="--",
    label="Available capacity + 40 MW",
    zorder=3,
)

ax.fill_between(
    df["date"],
    df["available_capacity_mw"],
    df["actual_peak_mw"],
    where=df["actual_peak_mw"] > df["available_capacity_mw"],
    color="#d62728",
    alpha=0.25,
    interpolate=True,
    label="Shortfall vs current capacity",
    zorder=1,
)
ax.fill_between(
    df["date"],
    df["capacity_plus_40"],
    df["actual_peak_mw"],
    where=df["actual_peak_mw"] > df["capacity_plus_40"],
    color="#8c1b13",
    alpha=0.60,
    interpolate=True,
    label="Shortfall remaining after +40 MW",
    zorder=2,
)

exceed_now = df[df["actual_peak_mw"] > df["available_capacity_mw"]]
ax.scatter(
    exceed_now["date"],
    exceed_now["actual_peak_mw"],
    color="#d62728",
    s=45,
    zorder=5,
)

max_row = df.loc[df["actual_peak_mw"].idxmax()]
ax.annotate(
    f"14 Jan peak: {max_row['actual_peak_mw']:.0f} MW\n"
    f"{max_row['shortfall_after_40']:.0f} MW short even with +40 MW",
    xy=(max_row["date"], max_row["actual_peak_mw"]),
    xytext=(max_row["date"] + pd.Timedelta(days=12), max_row["actual_peak_mw"] - 70),
    fontsize=9,
    arrowprops=dict(arrowstyle="->", color="black", lw=0.8),
    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="0.7", alpha=0.95),
    zorder=6,
)

n_now = int((df["shortfall_now"] > 0).sum())
n_after = int((df["shortfall_after_40"] > 0).sum())
max_now = df["shortfall_now"].max()
max_after = df["shortfall_after_40"].max()

summary = (
    "Shortfall days:\n"
    f"  Current: {n_now} days (max {max_now:.0f} MW)\n"
    f"  With +40 MW: {n_after} days (max {max_after:.0f} MW)\n"
    "Jan 14 still needs imports / more capacity."
)
ax.text(
    0.985,
    0.975,
    summary,
    transform=ax.transAxes,
    ha="right",
    va="top",
    fontsize=8.8,
    bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="0.6", alpha=0.95),
    zorder=7,
)

ax.set_title(
    "Would 40 MW of extra peak capacity cover the winter shortfalls?",
    fontsize=13,
    weight="bold",
    pad=10,
)
ax.set_ylabel("Peak demand / capacity (MW)")
ax.set_xlim(pd.Timestamp("2025-12-01"), pd.Timestamp("2026-03-01"))
ax.set_ylim(540, 1040)
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.grid(axis="y", alpha=0.3, linestyle=":")

handles, labels = ax.get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=8, frameon=False)
fig.subplots_adjust(left=0.09, right=0.98, top=0.91, bottom=0.20)
