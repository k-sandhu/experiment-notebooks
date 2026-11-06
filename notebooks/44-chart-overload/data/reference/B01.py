import pandas as pd
import matplotlib.pyplot as plt

HL, GREY = "#C0392B", "#9AA0A6"
df = pd.read_csv("data.csv")
rate = df.pivot(index="month", columns="plan", values="cancellation_rate_pct")
others = rate.drop(columns="Family").mean(axis=1)
x = list(range(len(rate)))
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(x[:-1], rate["Family"].iloc[:-1], color=HL, lw=3, marker="o")
ax.plot(x[-2:], rate["Family"].iloc[-2:], color=HL, lw=2, ls=":", marker="o", mfc="white")
ax.plot(x[:-1], others.iloc[:-1], color=GREY, lw=2)
ax.axvline(5.5, color="#555", lw=1, ls="--")
pre, post = rate["Family"].iloc[:6].mean(), rate["Family"].iloc[6:11].mean()
ax.text(2.5, pre + 0.35, f"average {pre:.1f}%", color=HL, fontsize=10.5, ha="center")
ax.text(8, post - 0.8, f"average {post:.1f}%", color=HL, fontsize=10.5, ha="center", fontweight="bold")
ax.text(5.6, 7.6, "Price \\$79 to \\$89\n1 April", fontsize=10, va="top", color="#333")
ax.text(10.1, rate["Family"].iloc[-2] + 0.3, "Family plan", color=HL, fontsize=11, fontweight="bold", ha="right")
ax.text(10.1, others.iloc[-2] - 0.5, "Other plans (average)", color=GREY, fontsize=11, ha="right")
ax.text(11, rate["Family"].iloc[-1] - 1.2, "September covers\n1-14 Sep only:\nnot a recovery", fontsize=9.5, ha="center", color="#333")
fam = df[df.plan == "Family"].set_index("month").active_subscribers
ax.set_title("Family-plan cancellations doubled after the April price rise", fontsize=15, loc="left", pad=28)
ax.text(0, 1.02, f"Monthly cancellation rate. Family subscribers fell from {fam['2026-04']:,} (1 Apr) to {fam['2026-09']:,} (1 Sep), "
        f"{(fam['2026-09'] / fam['2026-04'] - 1) * 100:.0f}%.", transform=ax.transAxes, fontsize=11, color="#333")
ax.set_xticks(x, [pd.Period(m).strftime("%b\n%Y") if pd.Period(m).month in (10, 1) else pd.Period(m).strftime("%b") for m in rate.index])
ax.set_ylim(0, 8)
ax.set_ylabel("Cancellations, % of subscribers per month")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
