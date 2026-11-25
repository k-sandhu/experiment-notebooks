import pandas as pd
import matplotlib.pyplot as plt

HL, GREY = "#C0392B", "#9AA0A6"
df = pd.read_csv("data.csv")
d30 = df[df.day == 30].set_index("signup_month")
coh = df.drop_duplicates("signup_month").set_index("signup_month")
x = list(range(len(d30)))
fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(x, d30.retention_pct, color=[HL if v == "new" else GREY for v in d30.onboarding_version])
old = d30[d30.onboarding_version == "old"].retention_pct.mean()
new = d30.loc[["2026-06", "2026-07", "2026-08"]].retention_pct.mean()
ax.plot([-0.4, 4.4], [old, old], color="#333", lw=1.2)
ax.text(2, old + 0.8, f"Old onboarding: {old:.1f}%", ha="center", fontweight="bold", color="#333")
ax.plot([4.6, 7.4], [new, new], color="#333", lw=1.2)
ax.text(6, new + 0.8, f"New onboarding: {new:.1f}%", ha="center", fontweight="bold", color=HL)
ax.axvspan(4.5, 7.5, color="#F5B7B1", alpha=0.25, lw=0)
ax.text(6, 2, "TV campaign Jun-Aug", ha="center", fontsize=9.5, color="#333")
ax.set_xticks(x, [pd.Period(m).strftime("%b") for m in d30.index])
ax.set_ylim(0, 38)
ax.set_ylabel("Users still active on day 30, %")
po = coh[coh.onboarding_version == "old"].paid_conversion_30d_pct.mean()
pn = coh.loc[["2026-06", "2026-07", "2026-08"]].paid_conversion_30d_pct.mean()
ax.set_title(f"The new onboarding lifted day-30 retention from {old:.0f}% to {new:.0f}%", fontsize=15, loc="left", pad=28)
ax.text(0, 1.02, f"2026 sign-up cohorts. Paid conversion within 30 days rose from {po:.1f}% to {pn:.1f}%. September, after the "
        f"campaign, still reached {d30.loc['2026-09', 'retention_pct']:.1f}%.", transform=ax.transAxes, fontsize=10.5, color="#333")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
