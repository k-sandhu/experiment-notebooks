import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Urgent patients only: longest waits for urgent cases are the decision-relevant signal.
# Northgate starts its clock at registration (about +15 min vs triage), so put it on the same basis.
urgent = df[df["triage_category"] == "Urgent"].copy()
urgent["median_wait_adj"] = urgent["median_wait_min"] - urgent["wait_clock_starts_at"].eq("registration") * 15
urgent = urgent.sort_values("median_wait_adj")  # ascending, so the longest wait is on top

riverside_val = float(urgent.loc[urgent["hospital"] == "Riverside", "median_wait_adj"].iloc[0])
other_avg = float(urgent.loc[urgent["hospital"] != "Riverside", "median_wait_adj"].mean())

strong = "#C62828"
grey = "#BDBDBD"
colors = [strong if h == "Riverside" else grey for h in urgent["hospital"]]

fig, ax = plt.subplots(figsize=(10, 6))

ax.barh(urgent["hospital"], urgent["median_wait_adj"], color=colors, height=0.62)

ax.set_xlim(0, 68)
ax.set_xlabel("Median wait to first be seen by a doctor (minutes)", fontsize=11)
ax.set_title(
    f"Riverside should get the extra triage nurses:\n"
    f"urgent patients wait {riverside_val:.0f} minutes — about twice as long as elsewhere",
    loc="left", fontsize=16, fontweight="bold", pad=16,
)

# Label only the number that is part of the message.
ax.text(
    riverside_val + 1.2, len(urgent) - 1, f"{riverside_val:.0f} min",
    va="center", ha="left", fontsize=12, fontweight="bold", color=strong,
)

# Context for "twice as long".
ax.axvline(other_avg, color="#666666", linestyle="--", linewidth=1.2)
ax.text(
    other_avg + 1.5, 0.15, f"Average of other\nhospitals: {other_avg:.0f} min",
    va="center", ha="left", fontsize=10, color="#444444",
)

for label in ax.get_yticklabels():
    label.set_fontsize(12)
    if label.get_text() == "Riverside":
        label.set_fontweight("bold")
        label.set_color(strong)

ax.tick_params(axis="x", labelsize=11)
ax.xaxis.grid(True, color="#E6E6E6", linewidth=0.8)
ax.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)

fig.text(
    0.01, 0.01,
    "Urgent patients only, July–September 2026  •  Northgate adjusted down 15 min: its clock starts at registration, not triage.",
    fontsize=9, color="#555555", ha="left",
)

plt.tight_layout(rect=[0, 0.05, 1, 1])
