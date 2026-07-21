# Historial de Cambios — paper_conescapan2026.tex

---

## Ronda 1 — Revisión metodológica inicial (2026-07-03)

### Experimentos ejecutados
- Bandit v1.9.x contra `vulnerable_api/`: 4 hallazgos LOW (B105/B106 — contraseñas hardcodeadas en seed.py y SECRET_KEY). Cobertura OWASP API Top 10: 0 categorías.
- Semgrep `p/django` (27 reglas) contra `vulnerable_api/`: 0 hallazgos. Ruleset cubre CSRF/SQLi, no patrones DRF.
- Evaluación externa: `encode/rest-framework-tutorial` — 4 hallazgos: 3 TP, 1 FP (API2-NO-JWT-CONFIG en proyecto sin JWT). Precision=0.75.

### Cambios en el paper
| Sección | Cambio |
|---------|--------|
| Abstract | "detected 100% of five planted categories" → "precision=1.00/recall=1.00 controlled; precision=0.75 external" |
| Section IV | Renombrada "Results" → "Evaluation"; nueva subsección "Experimental Setup and Ground Truth" |
| Table II (nueva) | Ground truth: 26 instancias plantadas por categoría (estático/dinámico) |
| Table III (nueva) | Precision / Recall / F1 por analizador y entorno |
| Subsección nueva | "External Project Evaluation" con análisis del DRF tutorial |
| Table IV (nueva) | Comparación vs Bandit, Semgrep, ZAP — ambas detectan 0 de 6 categorías OWASP |
| Section V Discussion | Párrafo nuevo: causa raíz del FP (API2-NO-JWT-CONFIG), análisis de API1-BOLA-URL |
| Section VI Conclusions | Reescrita con números reales P/R/F1 |
| Contributions | Actualizada para mencionar comparación con herramientas relacionadas |
| \bibitem{drftutorial} | Referencia nueva para el proyecto externo evaluado |

---

## Ronda 2 — Revisión profunda del director (2026-07-16)

### Observaciones del director que requieren cambios

1. **Heurísticas débiles**: Las reglas estáticas son indicadores de riesgo (*risk indicators* / *security smells*), no vulnerabilidades confirmadas. Reformular toda la terminología.
2. **FP en análisis dinámico**: HTTP 200 sin token puede ser correcto; BOLA asume configuración específica; is_admin reflejado ≠ persistido; 20 requests sin 429 ≠ API4 confirmado.
3. **RAG sin evaluación real**: 4 chunks + sección "Sources" no prueban calidad. Falta ablación (con vs. sin RAG) y evaluación humana con rúbrica.
4. **Novedad sobreafirmada**: RAG no es nuevo; el aporte es la integración local, trazable y orientada a hallazgos DRF.
5. **Errores visuales**: Fig 1 ("four-module" incorrecto), Fig 2 (flujo incompleto), Fig 4 (eje Y visible solo muestra LOW), Fig 5 (KB indexing y LLM mezclados).
6. **Reproducibilidad**: Faltan versiones de software, configuración de Ollama, cuantización de Mistral.
7. **Cambios obligatorios**: 3+ proyectos externos, métricas por regla, citas de Semgrep/Spectral/42Crunch, eliminar afirmación GPU "3-5s".

### Plan de ejecución — Ronda 2

| Tarea | Estado |
|-------|--------|
| Crear CAMBIOS.md | ✅ |
| Evaluar 2 proyectos DRF externos adicionales (drfx + drf-yasg) | ✅ |
| Calcular TP/FP/FN por regla (Table: Per-Rule Precision) | ✅ |
| Reformular reglas estáticas como risk indicators (Table I + texto) | ✅ |
| Añadir caveats al análisis dinámico (5 probes con assumptions) | ✅ |
| Ejecutar ablación RAG (5 findings con/sin RAG) → JSON guardados | ✅ |
| Añadir sección RAG Ablation Study + Table cuantitativa al paper | ✅ |
| Diseñar rúbrica 5-criterios + puntuar 5 recs (with/without RAG) | ✅ |
| Añadir Table rubric al paper (human eval, 1-3 scale) | ✅ |
| Corregir novedad RAG en paper (Discussion) | ✅ |
| Corregir Figura 1 (five-stage pipeline) | ✅ |
| Corregir Figura 2 (flujo RAG con "Recommendation + Sources cited") | ✅ |
| Corregir Figura 4 (timing: addplots separados por color por fase) | ✅ |
| Añadir tabla de reproducibilidad (Table: Software Versions) | ✅ |
| Agregar citas Semgrep, Spectral, 42Crunch | ✅ |
| Eliminar afirmación GPU "3-5s" sin medición | ✅ |
| Abstract actualizado: P=0.21 en 3 proyectos externos combinados | ✅ |
| Tabla External Project Evaluation (3 proyectos) | ✅ |
| Tabla Ground Truth (26 instancias plantadas) | ✅ |
| Reducir descripción de implementación, ampliar evaluación | ✅ |

### Ronda 2 — Resumen de cambios al paper (2026-07-16)

| Sección / Elemento | Cambio realizado |
|--------------------|-----------------|
| Abstract | P=0.75 (1 proyecto) → P=0.21 (3 proyectos combinados); rúbrica RAG: 1.72→2.80/3, halluc. 2/5→0/5 |
| Table I (Static Rules) | Añadida columna "FP condition"; encabezado "all outputs are risk indicators" |
| Dynamic Analyzer | 5 probes: cada una con documentación de su assumption/FP condition |
| Figura 1 (arch) | "four-module pipeline" → "five-stage processing pipeline" |
| Figura 2 (rag) | Nodo final: "Recommendation + Sources cited" |
| Figura 4 (timing) | Un solo addplot con mismo color → 4 addplots con colores distintos (Static/Dynamic/KB/LLM) |
| Table repro | Nueva: Python 3.12.8, Django 4.2, DRF 3.14, Ollama, Mistral Q4_K_M, etc. |
| Table ground truth | Nueva: 26 instancias plantadas por categoría |
| Table exteval | Nueva: DRF tutorial P=0.75, drfx P=0.50, drf-yasg P=0.08, Combined P=0.21 |
| Table perrule | Nueva: precisión por regla en proyectos externos; API2-JWT=0.00, API8=1.00, etc. |
| Table ablation | Nueva: RAG vs No-RAG; 959 vs 1567 chars avg; 0/5 vs 2/5 hallucinations |
| Table rubric | Nueva: rúbrica 5 criterios (TC/DS/OA/AC/ST, escala 1-3); RAG avg 2.80 vs no-RAG 1.72 |
| Section RAG Ablation | Nueva subsección \label{sec:ragablation} antes de Discussion; incluye rubric + análisis |
| Discussion | Análisis FP, corrección framing RAG, eliminado claim GPU, limitaciones ampliadas |
| Conclusions | Reescrita con P=0.21 externo, referencia a ablación, fixes proyectados P≥0.90 |
| Related Work | Citas añadidas: Semgrep, Spectral, 42Crunch |
| Bibliography | \bibitem nuevos: semgrep, spectral, fortytwoCrunch, drfx, drfyasg |
