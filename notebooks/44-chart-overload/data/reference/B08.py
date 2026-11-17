import pandas as pd
import matplotlib.pyplot as plt

HL, GREY = "#C0392B", "#9AA0A6"
df = pd.read_csv("data.csv", parse_dates=["date"])
cold = df.min_temp_c < -15
err = 100 * (df.actual_peak_mw / df.forecast_peak_mw - 1)
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df.date, df.forecast_peak_mw, color=GREY, lw=1.5)
ax.plot(df.date, df.actual_peak_mw, color="#333", lw=1.5)
ax.step(df.date, df.available_capacity_mw, where="mid", color="#2471A3", lw=1.5)
over = df[df.actual_peak_mw > df.available_capacity_mw]
ax.scatter(over.date, over.actual_peak_mw, color=HL, s=50, zorder=3)
ax.text(over.date.iloc[0] - pd.Timedelta(days=26), 1000, f"Over capacity on {len(over)} days\n(12-15 Jan)", color=HL, fontweight="bold")
ax.text(df.date.iloc[-1], 968, "Available capacity", color="#2471A3", ha="right", fontsize=10)
ax.text(pd.Timestamp("2026-01-18"), 870, "Unit 3 out for repair 10-16 Jan (-50 MW).\nWith it running, only 14 Jan exceeds capacity.",
        fontsize=9.5, color="#333")
ax.text(df.date.iloc[1], 850, "Actual", color="#333", fontsize=10)
ax.text(df.date.iloc[1], 600, "Forecast (grey)", color="#777", fontsize=10)
ax.set_ylim(560, 1060)
ax.set_ylabel("Daily peak demand, MW")
ax.set_title(f"On days below -15 °C demand ran {err[cold].mean():.0f}% above forecast, and it exceeded capacity on 4 days",
             fontsize=13.5, loc="left", pad=12)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
