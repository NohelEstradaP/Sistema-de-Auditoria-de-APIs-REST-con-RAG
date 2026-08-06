"""
Generate diagram PNGs for the anteproyecto.
Outputs to the project root at 150 dpi.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

OUT_DIR = os.path.join(os.path.dirname(__file__), "..")

def draw_box(ax, x, y, w, h, text, color="#2563EB", textcolor="white", fontsize=9):
    rect = mpatches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02",
        linewidth=1.2,
        edgecolor="#1e3a5f",
        facecolor=color,
        zorder=3,
    )
    ax.add_patch(rect)
    ax.text(
        x + w / 2, y + h / 2, text,
        ha="center", va="center",
        color=textcolor, fontsize=fontsize,
        fontweight="bold", wrap=True, zorder=4,
        multialignment="center",
    )

def arrow(ax, x0, y0, x1, y1):
    ax.annotate(
        "", xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(arrowstyle="->", color="#374151", lw=1.5),
        zorder=5,
    )


# ── Figura 1: Arquitectura del sistema ───────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 4))
ax.set_xlim(0, 10)
ax.set_ylim(0, 4)
ax.axis("off")
fig.patch.set_facecolor("white")

colors = ["#1d4ed8", "#0369a1", "#0f766e", "#7c3aed", "#b45309"]
labels = [
    "Analizador\nEstático\n(AST)",
    "Analizador\nDinámico\n(HTTP)",
    "Base de\nConocimiento\n(ChromaDB)",
    "Pipeline\nRAG / LLM\n(Mistral 7B)",
    "Generador\nde Reportes\n(PDF/HTML)",
]
xs = [0.3, 2.1, 3.9, 5.7, 7.5]
bw, bh = 1.5, 2.2
by = 0.9

for i, (x, lbl, col) in enumerate(zip(xs, labels, colors)):
    draw_box(ax, x, by, bw, bh, lbl, color=col, fontsize=8.5)
    if i < len(xs) - 1:
        arrow(ax, x + bw, by + bh / 2, xs[i + 1], by + bh / 2)

# Knowledge base feeds into RAG
arrow(ax, xs[2] + bw / 2, by + bh, xs[3] + bw / 2, by + bh + 0.5)
ax.text(xs[3] + bw / 2, by + bh + 0.6, "Recuperación\nvectorial",
        ha="center", va="bottom", fontsize=7, color="#374151")

# Source arrow into Static
ax.annotate("", xy=(xs[0], by + bh / 2), xytext=(0.0, by + bh / 2),
            arrowprops=dict(arrowstyle="->", color="#374151", lw=1.5))
ax.text(0.02, by + bh / 2 + 0.2, "Código\nfuente", ha="left", va="bottom",
        fontsize=7.5, color="#374151")

# Report output
ax.annotate("", xy=(xs[4] + bw + 0.1, by + bh / 2), xytext=(xs[4] + bw, by + bh / 2),
            arrowprops=dict(arrowstyle="->", color="#374151", lw=1.5))
ax.text(xs[4] + bw + 0.12, by + bh / 2, "Reporte", ha="left", va="center",
        fontsize=7.5, color="#374151")

ax.set_title("Arquitectura del sistema de auditoría de seguridad",
             fontsize=10, pad=8, color="#111827")
plt.tight_layout(pad=0.4)
out1 = os.path.join(OUT_DIR, "figura1_arquitectura.png")
fig.savefig(out1, dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Saved: {out1}")


# ── Figura 2: Flujo del pipeline RAG ─────────────────────────────────────────
fig2, ax2 = plt.subplots(figsize=(10, 3.2))
ax2.set_xlim(0, 10)
ax2.set_ylim(0, 3.2)
ax2.axis("off")
fig2.patch.set_facecolor("white")

steps = [
    ("Hallazgo\ndetectado", "#1d4ed8"),
    ("Consulta\nvectorial", "#0369a1"),
    ("Recuperación\nChromaDB\n(top-4)", "#0f766e"),
    ("Prompt\nenriquecido", "#7c3aed"),
    ("Ollama\nMistral 7B", "#b45309"),
    ("Reporte +\nCitaciones", "#065f46"),
]
sw, sh = 1.35, 1.6
sy = 0.8
gap = (10 - len(steps) * sw) / (len(steps) + 1)

for i, (lbl, col) in enumerate(steps):
    sx = gap + i * (sw + gap)
    draw_box(ax2, sx, sy, sw, sh, lbl, color=col, fontsize=8)
    if i < len(steps) - 1:
        nx = gap + (i + 1) * (sw + gap)
        arrow(ax2, sx + sw, sy + sh / 2, nx, sy + sh / 2)

ax2.set_title("Flujo del pipeline de Generación Aumentada por Recuperación (RAG)",
              fontsize=10, pad=8, color="#111827")
plt.tight_layout(pad=0.4)
out2 = os.path.join(OUT_DIR, "figura2_rag_flow.png")
fig2.savefig(out2, dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig2)
print(f"Saved: {out2}")
