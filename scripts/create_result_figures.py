"""
Generate result chart PNGs for the Trabajo de Graduacion (Fase 1 - Presentacion de Resultados).
Data source: paper_conescapan2026.tex tables + results/ablation_rubric.json.
Outputs to the project root at 150 dpi, same visual style as scripts/create_figures.py.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = os.path.join(os.path.dirname(__file__), "..")

COLOR_STATIC = "#1d4ed8"
COLOR_DYNAMIC = "#0f766e"
COLOR_OURS = "#1d4ed8"
COLOR_OTHER = "#94a3b8"
COLOR_WITH_RAG = "#7c3aed"
COLOR_NO_RAG = "#b45309"
TEXT_DARK = "#111827"

plt.rcParams.update({
    "font.size": 9,
    "axes.edgecolor": "#374151",
    "axes.labelcolor": TEXT_DARK,
    "text.color": TEXT_DARK,
    "xtick.color": "#374151",
    "ytick.color": "#374151",
})


# ── Grafica 1: hallazgos por categoria OWASP (estatico vs dinamico) ─────────
categories = ["API1", "API2", "API3", "API4", "API5", "API8"]
static_counts = [4, 8, 5, 1, 0, 1]
dynamic_counts = [1, 3, 1, 1, 1, 0]

fig, ax = plt.subplots(figsize=(6.2, 3.6))
x = np.arange(len(categories))
ax.bar(x, static_counts, label="Estático (AST)", color=COLOR_STATIC, edgecolor="#1e3a5f")
ax.bar(x, dynamic_counts, bottom=static_counts, label="Dinámico (HTTP)", color=COLOR_DYNAMIC, edgecolor="#0b4a3f")
for i, (s, d) in enumerate(zip(static_counts, dynamic_counts)):
    total = s + d
    if total > 0:
        ax.text(i, total + 0.15, str(total), ha="center", fontsize=8, color=TEXT_DARK)
ax.set_xticks(x)
ax.set_xticklabels(categories)
ax.set_ylabel("Número de hallazgos")
ax.set_xlabel("Categoría OWASP API Top 10 (2023)")
ax.set_ylim(0, 13)
ax.set_title("Distribución de hallazgos por categoría OWASP\n(entorno controlado, 26 instancias sembradas)", fontsize=10)
ax.legend(frameon=False, loc="upper right", fontsize=8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout(pad=0.5)
out = os.path.join(OUT_DIR, "grafica1_hallazgos_owasp.png")
fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Saved: {out}")


# ── Grafica 2: cobertura OWASP por herramienta ──────────────────────────────
tools = ["Herramienta\npropia", "Bandit", "Semgrep\n(p/django)", "OWASP ZAP"]
coverage = [6, 0, 0, 3]
partial = [False, False, False, True]
colors = [COLOR_OURS if t == "Herramienta\npropia" else COLOR_OTHER for t in tools]

fig, ax = plt.subplots(figsize=(6.2, 3.6))
bars = ax.bar(tools, coverage, color=colors, edgecolor="#374151")
for i, (bar, v, p) in enumerate(zip(bars, coverage, partial)):
    label = f"{v} / 6" + (" (parcial)" if p else "")
    ax.text(bar.get_x() + bar.get_width() / 2, v + 0.15, label, ha="center", fontsize=8)
ax.set_ylabel("Categorías OWASP cubiertas (de 6 objetivo)")
ax.set_ylim(0, 7)
ax.set_title("Cobertura de las 6 categorías OWASP objetivo por herramienta\n(evaluado contra vulnerable_api/)", fontsize=10)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout(pad=0.5)
out = os.path.join(OUT_DIR, "grafica2_comparacion_herramientas.png")
fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Saved: {out}")


# ── Grafica 3: tiempos de ejecucion por fase (escala log) ───────────────────
phases = ["Estático", "Dinámico", "Indexado KB\n(una vez)", "LLM\n(24 recomendaciones)"]
times = [0.01, 0.13, 112, 1680]
colors3 = [COLOR_STATIC, COLOR_DYNAMIC, "#9333ea", "#b45309"]

fig, ax = plt.subplots(figsize=(6.2, 3.6))
y = np.arange(len(phases))
bars = ax.barh(y, times, color=colors3, edgecolor="#374151")
ax.set_xscale("log")
ax.set_xlim(0.005, 5000)
for bar, t in zip(bars, times):
    label = f"{t:g} s"
    ax.text(bar.get_width() * 1.15, bar.get_y() + bar.get_height() / 2, label, va="center", fontsize=8)
ax.set_yticks(y)
ax.set_yticklabels(phases)
ax.set_xlabel("Tiempo (segundos, escala logarítmica)")
ax.set_title("Tiempo de ejecución por fase (Apple M3, 16 GB RAM, sin GPU)", fontsize=10)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout(pad=0.5)
out = os.path.join(OUT_DIR, "grafica3_tiempos_ejecucion.png")
fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Saved: {out}")


# ── Grafica 4: rubrica de evaluacion humana con vs sin RAG ──────────────────
criteria = ["TC\n(Corrección)", "DS\n(Especificidad\nDRF)", "OA\n(Alineación\nOWASP)", "AC\n(Accionabilidad)", "ST\n(Trazabilidad\nde fuentes)"]
with_rag = [3.0, 2.8, 2.4, 2.8, 3.0]
no_rag = [2.2, 2.0, 1.8, 1.6, 1.4]

fig, ax = plt.subplots(figsize=(7.0, 3.8))
x = np.arange(len(criteria))
w = 0.35
ax.bar(x - w / 2, with_rag, width=w, label="Con RAG (prom. 2.80)", color=COLOR_WITH_RAG, edgecolor="#4c1d95")
ax.bar(x + w / 2, no_rag, width=w, label="Sin RAG (prom. 1.80)", color=COLOR_NO_RAG, edgecolor="#78350f")
ax.set_xticks(x)
ax.set_xticklabels(criteria, fontsize=7.5)
ax.set_ylabel("Puntuación (escala 1–3)")
ax.set_ylim(0, 3.6)
ax.set_title("Rúbrica de evaluación humana de recomendaciones — con vs. sin RAG\n(5 hallazgos representativos, Mistral 7B)", fontsize=10)
ax.legend(frameon=False, loc="upper right", fontsize=8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout(pad=0.5)
out = os.path.join(OUT_DIR, "grafica4_rubrica_rag.png")
fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Saved: {out}")


# ── Grafica 5: alucinaciones con vs sin RAG ──────────────────────────────────
labels = ["Con RAG", "Sin RAG"]
hallu = [0, 2]
total = 5
colors5 = [COLOR_WITH_RAG, COLOR_NO_RAG]

fig, ax = plt.subplots(figsize=(4.6, 3.4))
bars = ax.bar(labels, hallu, color=colors5, edgecolor="#374151", width=0.5)
for bar, h in zip(bars, hallu):
    ax.text(bar.get_x() + bar.get_width() / 2, h + 0.05, f"{h} de {total}", ha="center", fontsize=9)
ax.set_ylabel("Recomendaciones con alucinación detectada")
ax.set_ylim(0, 3)
ax.set_yticks([0, 1, 2, 3])
ax.set_title("Alucinaciones detectadas por condición\n(5 hallazgos evaluados)", fontsize=10)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout(pad=0.5)
out = os.path.join(OUT_DIR, "grafica5_alucinaciones.png")
fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Saved: {out}")
