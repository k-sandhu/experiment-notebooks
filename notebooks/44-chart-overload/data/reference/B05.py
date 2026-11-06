import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

HL, GREY = "#C0392B", "#9AA0A6"
df = pd.read_csv("data.csv")
order = ["Swiftline", "Northway", "ParcelPro"]
rng = np.random.default_rng(0)
fig, ax = plt.subplots(figsize=(10, 6))
for i, c in enumerate(order):
    h = df[df.courier == c].actual_hours.to_numpy()
    late = h > 48
    y = i + rng.uniform(-0.18, 0.18, len(h))
    ax.scatter(h[~late], y[~late], s=16, color=GREY, alpha=0.7)
    ax.scatter(h[late], y[late], s=22, color=HL)
    ax.plot([np.median(h)] * 2, [i - 0.28, i + 0.28], color="#333", lw=2)
    ax.text(81, i, f"{100 * late.mean():.0f}% over 48 h", va="center", ha="left", fontsize=11,
            color=HL if c == "Swiftline" else "#333", fontweight="bold" if c == "Swiftline" else "normal")
ax.axvline(48, color=HL, lw=1.2, ls="--")
ax.text(48.5, 2.45, "48-hour cold-pack limit", color=HL, fontsize=10)
ax.set_yticks(range(3), ["Swiftline", "Northway", "ParcelPro\n(only 40 deliveries)"])
ax.invert_yaxis()
ax.set_xlim(0, 95)
ax.set_xlabel("Hours from dispatch to delivery (each dot is one delivery; black line = median)")
ax.set_title("Swiftline is fastest on a typical day, but 14% of its deliveries break the 48-hour limit",
             fontsize=13.5, loc="left", pad=12)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", alpha=0.25)
fig.tight_layout()
