import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

df = pd.read_csv("data.csv")

# --- Groups: separate September (new onboarding, TV campaign over) ---
is_old = df["onboarding_version"] == "old"
is_new_tv = df["signup_month"].isin(["2026-06", "2026-07", "2026-08"])
is_sept = df["signup_month"] == "2026-09"

def retention_curve(mask):
    g = (
        df[mask]
        .groupby("day")
        .agg(retained=("retained_users", "sum"), size=("cohort_size", "sum"))
    )
    return g.index.to_numpy(), (100 * g["retained"] / g["size"]).to_numpy()

x_old, y_old = retention_curve(is_old)
x_new, y_new = retention_curve(is_new_tv)
x_sept, y_sept = retention_curve(is_sept)

def at_day(x, y, day):
    return float(y[list(x).index(day)])

old30, new30, sept30 = at_day(x_old, y_old, 30), at_day(x_new, y_new, 30), at_day(x_sept, y_sept, 30)

# Cohort-level 30-day outcomes (one row per cohort)
cohorts = df.drop_duplicates("signup_month").sort_values("signup_month")
c_old = cohorts[cohorts["onboarding_version"] == "old"]
c_new = cohorts[cohorts["signup_month"].isin(["2026-06", "2026-07", "2026-08"])]
wavg = lambda d, col: np.average(d[col], weights=d["cohort_size"])
paid_old, paid_new = wavg(c_old, "paid_conversion_30d_pct"), wavg(c_new, "paid_conversion_30d_pct")
less_old, less_new = wavg(c_old, "avg_lessons_first_30d"), wavg(c_new, "avg_lessons_first_30d")

d30 = df[df["day"] == 30].sort_values("signup_month").copy()
d30["label"] = pd.to_datetime(d30["signup_month"]).dt.strftime("%b")

# --- Figure ---
GREY, TEAL, ORANGE = "#8a8d93", "#0e7c6b", "#d97706"
fig = plt.figure(figsize=(10, 6))
gs = GridSpec(1, 2, width_ratios=[1.55, 1.0], wspace=0.30)
ax = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])
fig.subplots_adjust(left=0.07, right=0.97, top=0.80, bottom=0.20)

fig.suptitle("Keep the new onboarding — the retention gain survives the end of the TV campaign",
             x=0.07, y=0.97, ha="left", fontsize=15.5, fontweight="bold")
fig.text(0.07, 0.915,
         f"Day-30 retention:  {old30:.1f}% old (Jan–May)  →  {new30:.1f}% new (Jun–Aug, with TV)  →  {sept30:.1f}% in September (new, no TV)",
         fontsize=10.5, color="#333333")

# --- Left: retention curves ---
ax.plot(x_old, y_old, "-o", color=GREY, lw=2.6, ms=5, label="Old onboarding — Jan–May (5 cohorts)")
ax.plot(x_new, y_new, "-o", color=TEAL, lw=3.2, ms=6, label="New onboarding — Jun–Aug (TV campaign running)")
ax.plot(x_sept, y_sept, "--s", color=ORANGE, lw=2.6, ms=6,
        label="New onboarding — September only (after TV ended)")

ax.annotate("", xy=(33, new30), xytext=(33, old30),
            arrowprops=dict(arrowstyle="<->", color=TEAL, lw=1.6))
ax.text(35, (old30 + new30) / 2, f"+{new30 - old30:.1f} pts\nat Day 30",
        fontsize=10, fontweight="bold", color=TEAL, va="center")
for x, y, c, lab in [(30, old30, GREY, f"{old30:.1f}%"), (30, new30, TEAL, f"{new30:.1f}%"),
                     (30, sept30, ORANGE, f"Sept: {sept30:.1f}%")]:
    ax.annotate(lab, (x, y), textcoords="offset points", xytext=(-4, 8 if c != GREY else -16),
                fontsize=9.5, fontweight="bold", color=c)
ax.text(1.5, 63, "Day 1 ≈ 70% for every cohort:\nthe gap opens after sign-up", fontsize=8.5, color="#555555")

ax.set_xticks([1, 7, 14, 30, 60, 90])
ax.set_xlabel("Days since sign-up", fontsize=10)
ax.set_ylabel("% of cohort still active", fontsize=10)
ax.set_ylim(0, 78)
ax.grid(axis="y", color="#dddddd", lw=0.7)
ax.set_axisbelow(True)
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
ax.legend(loc="upper right", frameon=False, fontsize=8.3)
ax.set_title("Retention by days since sign-up (cohort-size weighted)", fontsize=10.5, loc="left")

# --- Right: every cohort at Day 30 ---
colors = [ORANGE if m == "2026-09" else (TEAL if v == "new" else GREY)
          for m, v in zip(d30["signup_month"], d30["onboarding_version"])]
bars = ax2.bar(range(len(d30)), d30["retention_pct"], color=colors, edgecolor="white")
bars[-1].set_hatch("//")
bars[-1].set_edgecolor("white")
for i, v in enumerate(d30["retention_pct"]):
    ax2.text(i, v + 0.7, f"{v:.1f}", ha="center", fontsize=8)
ax2.axhline(old30, color=GREY, ls="--", lw=1.2)
ax2.axhline(new30, color=TEAL, ls="--", lw=1.2)
ax2.text(0, old30 - 2.6, f"old avg {old30:.1f}%", fontsize=8, color=GREY)
ax2.text(0, new30 + 0.8, f"new Jun–Aug avg {new30:.1f}%", fontsize=8, color=TEAL, fontweight="bold")
ax2.axvline(4.5, color="#333333", lw=1.2)
ax2.text(4.5, 36.5, "new flow live 1 Jun\n+ TV Jun–Aug", ha="center", fontsize=8, color="#333333")
ax2.text(8, 33.5, "no TV", ha="center", fontsize=8.5, fontweight="bold", color=ORANGE)
ax2.set_xticks(range(len(d30)))
ax2.set_xticklabels(d30["label"], fontsize=9)
ax2.set_ylim(0, 40)
ax2.set_ylabel("Day-30 retention (%)", fontsize=10)
ax2.set_xlabel("Sign-up cohort", fontsize=10)
ax2.grid(axis="y", color="#dddddd", lw=0.7)
ax2.set_axisbelow(True)
for s in ["top", "right"]:
    ax2.spines[s].set_visible(False)
ax2.set_title("Every cohort at Day 30 — no exceptions", fontsize=10.5, loc="left")

# --- Supporting outcomes + caveats ---
fig.text(0.07, 0.085,
         f"First 30 days, Jun–Aug vs Jan–May:   paid conversion {paid_old:.1f}% → {paid_new:.1f}%   •   "
         f"lessons per user {less_old:.1f} → {less_new:.1f} (+{100 * (less_new / less_old - 1):.0f}%)"
         f"        Recommendation: KEEP the new flow",
         fontsize=10, fontweight="bold", color=TEAL,
         bbox=dict(boxstyle="round,pad=0.45", facecolor="#e6f3f0", edgecolor=TEAL))
fig.text(0.07, 0.025,
         "Retained on day N = completed a lesson on day N or later. Data to 2 Nov 2026, so August runs to day 60 and "
         "September to day 30 only — lines stop there.\nSeptember cannot prove the TV campaign played no part in Jun–Aug, "
         "but a gain of this size with the campaign off is not explained by it.",
         fontsize=7.5, color="#666666")
