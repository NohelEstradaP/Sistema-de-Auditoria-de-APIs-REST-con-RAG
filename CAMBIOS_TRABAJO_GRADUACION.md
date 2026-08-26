# Cambios: Anteproyecto Aprobado → Trabajo de Graduación (Borrador 1)

Comparación entre `Anteproyecto Didvin Nohel Estrada Pineda APROBADO. L. DE ALVAREZ.docx` (aprobado, base de partida) y `Trabajo_de_Graduacion_Borrador1.docx` (estado actual, tras Fase 0 y Fase 1 del plan de trabajo).

Referencia normativa: *Guía de Trabajo de Graduación PTI 10 2026* (Facultad de Ingeniería, UNIS) — el documento final sigue una estructura distinta a la del anteproyecto (Anexo 2 de la guía).

---

## 1. Resumen general

| | Anteproyecto | Borrador 1 |
|---|---|---|
| Párrafos totales | 469 | 706 |
| Notas al pie (ISO 690) | 78 | 80 |
| Imágenes embebidas | 2 (Figura 1 y 2) | 9 (+1 figura, +5 gráficas nuevas, +1 captura de reporte) |
| Sección 4 | "RESULTADOS ESPERADOS" (prospectivo) | "PRESENTACIÓN DE RESULTADOS" (datos reales obtenidos) |
| Sección 5 | "CRONOGRAMA PRELIMINAR" | *(eliminada)* |
| Front matter | Solo portada simple | Portada formato Trabajo de Graduación + 6 páginas nuevas |

---

## 2. Front matter — nuevo

**Antes:** la portada decía "ANTEPROYECTO" + título + nombre + fecha. No había nada más antes de "INTRODUCCIÓN".

**Ahora:**
- Portada reescrita a formato Trabajo de Graduación (Anexo 6 de la guía): "Trabajo de Graduación", "Presentado al Consejo de la Facultad de Ingeniería...", título de Ingeniero, "Por", nombre del autor, "Asesorado por: [pendiente]", fecha "[pendiente]".
- 6 páginas nuevas insertadas (cada una con salto de página), todas marcadas **"Pendiente"** — se completan en la Fase 4:
  1. Carta de autorización de impresión
  2. Carta de aprobación del asesor
  3. Agradecimiento
  4. Índice General
  5. Índice de Ilustraciones
  6. Resumen

**Pendiente real de tu parte:** nombre del asesor y fecha final para la portada.

---

## 3. Introducción — cambio menor

**Antes:** las dos primeras citas del documento ("Atlidakis et al. (2019)" y "Zhou et al. (2019)") no tenían nota al pie — quedaban solo como texto narrativo con el año entre paréntesis.

**Ahora:** se agregaron esas 2 notas al pie (citas completas) y se ajustaron a "Op. Cit." las notas que antes eran la primera mención de esas mismas fuentes, más adelante en el Marco Teórico (ya no son la primera cita).

---

## 4. Marco de Referencia (1.1–1.3) — sin cambios de fondo

El contenido teórico (Antecedentes, Situación Actual, Marco Teórico 1.3.1–1.3.8) se mantiene igual al anteproyecto aprobado — ya estaba sólido. Las 78 notas al pie ISO 690 que ya existían (de una sesión de trabajo anterior) se conservaron intactas; las 2 figuras (arquitectura del sistema, flujo del pipeline RAG) ya estaban embebidas y no requirieron cambios.

---

## 5. Planteamiento del Problema (2.1–2.6) — sin cambios

Descripción del problema, objetivos, justificación, hipótesis, variables, alcance y limitaciones: iguales al anteproyecto aprobado.

---

## 6. Método (3.1–3.4) — sin cambios todavía

Sigue con el texto del anteproyecto, redactado de forma prospectiva ("se ejecutará"). **Pendiente para la Fase 2:** reescribirlo en pasado, con el procedimiento tal como realmente se ejecutó, y actualizar la tabla de instrumentos con las versiones reales de software.

---

## 7. Sección 4 — el cambio más grande: "RESULTADOS ESPERADOS" → "PRESENTACIÓN DE RESULTADOS"

**Antes:** 5 párrafos prospectivos ("A corto plazo... se espera obtener...", "A mediano plazo...", "A largo plazo..."), sin una sola tabla, cifra o gráfica — todo en condicional/futuro, sin datos reales.

**Ahora:** título cambiado, contenido reemplazado por completo con 8 subsecciones, datos reales tomados de `results/*.json`, `CAMBIOS.md` y `paper_conescapan2026.tex` (evaluaciones ya ejecutadas en julio 2026), y 6 imágenes nuevas generadas para este documento:

| Subsección | Contenido | Ilustración |
|---|---|---|
| 4.1 Instancias sembradas (ground truth) | 26 instancias, 6 categorías OWASP, división estático/dinámico | Cuadro No. 3 + Gráfica No. 1 |
| 4.2 Métricas — entorno controlado | TP=26, FP=0, FN=0, P=R=F1=1.00 | Tabla No. 1 |
| 4.3 Evaluación en proyectos externos | 3 proyectos (DRF tutorial, drfx, drf-yasg); P=0.75/0.50/0.08, combinada 0.21; precisión por regla (2 reglas en P=0.00) | Tabla No. 2, Tabla No. 3 |
| 4.4 Comparación con herramientas relacionadas | 6/6 categorías vs. Bandit (0) vs. Semgrep (0) vs. ZAP (≤3 parcial) | Cuadro No. 4 + Gráfica No. 2 |
| 4.5 Tiempo de ejecución | Estático 0.01s, dinámico 0.13s, indexado KB 112s, LLM 1680s/24 recs | Gráfica No. 3 |
| 4.6 Cobertura de pruebas unitarias | 119 tests (113 auditor + 6 vulnerable_api), 100% | Tabla No. 4 |
| 4.7 Estudio de ablación RAG | 959 vs. 1567 caracteres; 0/5 vs. 2/5 alucinaciones; rúbrica 2.80 vs. 1.80 | Tabla No. 5 + Gráfica No. 4 + Gráfica No. 5 |
| 4.8 Evidencia del reporte generado | Extracto real del reporte de auditoría (generado 1 jul 2026) | Figura No. 3 |

**Omitido a propósito:** la tabla ilustrativa de un solo hallazgo BOLA (equivalente a *tab:rag_ex* del paper) — se consideró redundante con la fila API1-BOLA de la Tabla No. 5.

---

## 8. Sección 5 — eliminada: "CRONOGRAMA PRELIMINAR"

El anteproyecto tenía una sección completa con una tabla de 9 semanas (jul–sep 2026) y 8 actividades. **Se eliminó por completo** — la guía del Trabajo de Graduación no incluye cronograma en el documento final (solo aplica al anteproyecto).

---

## 9. Bibliografía — sin cambios

Las 24 referencias ISO 690-2021 del anteproyecto se mantienen igual. Se actualizarán/completarán en la Fase 3 si la Discusión cita alguna fuente nueva.

---

## 10. Lo que falta (Fases 2, 3 y 4 del plan)

- **Fase 2:** reescribir el Método (3) en pasado + redactar la Discusión (5), confrontando estos resultados con el Marco de Referencia y las hipótesis.
- **Fase 3:** Conclusiones, Recomendaciones, Glosario (mín. 10 términos), Bibliografía final.
- **Fase 4:** Resumen final, portadas definitivas, índices con paginación real, verificación de estilo completa, corrección ortográfica final.

Ver `/Users/nohelestradap/.claude/plans/sorted-shimmying-cray.md` para el detalle de checkboxes de cada fase.
