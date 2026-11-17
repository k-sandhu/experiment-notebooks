import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

q = "My manager supports my growth"
mgr = df[df["question"] == q]
now = mgr[mgr["year"] == 2026].set_index("department")
prev = mgr[mgr["year"] == 2025].set_index("department")

# Lowest score at the top of the chart
now = now.sort_values("pct_favourable", ascending=True)
depts = now.index.tolist()
vals = now["pct_favourable"].values

focus = "Customer Support"
accent = "#C8102E"
grey = "#BDBDBD"
colors = [accent if d == focus else grey for d in depts]

fig, ax = plt.subplots(figsize=(10, 6))
y = range(len(depts))
ax.barh(y, vals, color=colors, height=0.65)
ax.invert_yaxis()

# Department labels, with the focus department highlighted
ax.set_yticks(list(y))
ax.set_yticklabels(depts, fontsize=11)
for tick, d in zip(ax.get_yticklabels(), depts):
    if d == focus:
        tick.set_color(accent)
        tick.set_fontweight("bold")

# Label only the number that carries the message
fy = depts.index(focus)
fval = now.loc[focus, "pct_favourable"]
pval = prev.loc[focus, "pct_favourable"]
ax.text(fval + 1.2, fy, f"{fval}%  (down from {pval}% in 2025)",
        va="center", ha="left", fontsize=11, color=accent, fontweight="bold")

# Honest scale
ax.set_xlim(0, 100)
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=10, color="#555555")
ax.set_xlabel("% favourable (agree or strongly agree), September 2026",
              fontsize=10, color="#555555")
ax.tick_params(axis="y", length=0)
ax.tick_params(axis="x", colors="#777777")
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#AAAAAA")
ax.xaxis.grid(True, color="#EEEEEE")
ax.set_axisbelow(True)

# Title and subtitle
fig.suptitle("Customer Support has by far the weakest manager support, falling 27 points to 44%",
             x=0.02, ha="left", fontsize=14, fontweight="bold", y=0.97)
ax.set_title("“My manager supports my growth”: % favourable by department, 2026 survey",
             loc="left", fontsize=11, color="#555555", pad=12)

# Caveat that changes how the Support bar should be read
n_now = int(now.loc[focus, "n_responses"])
hc = int(now.loc[focus, "headcount"])
rr_now = int(now.loc[focus, "response_rate_pct"])
rr_prev = int(prev.loc[focus, "response_rate_pct"])
fig.text(0.02, 0.025,
         f"Caveat: only {n_now} of {hc} Customer Support staff responded this year "
         f"({rr_now}% vs {rr_prev}% in 2025), so its score is less certain than other "
         f"departments' (77–85% response).",
         ha="left", fontsize=9.5, color="#444444", style="italic")

fig.subplots_adjust(left=0.18, right=0.97, top=0.85, bottom=0.17)
