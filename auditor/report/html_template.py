"""
Plantilla HTML para el reporte de auditoría.
Genera HTML completo con CSS embebido, listo para renderizar en navegador o convertir a PDF.
"""

from __future__ import annotations

import html
from typing import Union

from ..dynamic_analyzer.findings import DynamicFinding
from ..static_analyzer.findings import Finding
from .builder import AuditReport

_SEVERITY_COLOR = {
    "HIGH":   "#e53e3e",
    "MEDIUM": "#dd6b20",
    "LOW":    "#3182ce",
    "INFO":   "#718096",
}

_SEVERITY_BG = {
    "HIGH":   "#fff5f5",
    "MEDIUM": "#fffaf0",
    "LOW":    "#ebf8ff",
    "INFO":   "#f7fafc",
}

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px;
       color: #2d3748; background: #f7fafc; }
.page { max-width: 960px; margin: 0 auto; padding: 32px 24px; }

/* Header */
.header { background: #1a202c; color: white; padding: 28px 32px;
          border-radius: 8px; margin-bottom: 28px; }
.header h1 { font-size: 22px; font-weight: 700; margin-bottom: 6px; }
.header .meta { font-size: 12px; color: #a0aec0; }

/* Summary cards */
.summary { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 28px; }
.card { flex: 1; min-width: 120px; background: white; border-radius: 8px;
        padding: 16px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,.1); }
.card .num { font-size: 32px; font-weight: 700; line-height: 1; }
.card .lbl { font-size: 11px; color: #718096; margin-top: 4px; text-transform: uppercase; }
.card.high   .num { color: #e53e3e; }
.card.medium .num { color: #dd6b20; }
.card.low    .num { color: #3182ce; }
.card.info   .num { color: #718096; }
.card.total  .num { color: #1a202c; }

/* Section titles */
h2 { font-size: 16px; font-weight: 700; color: #1a202c;
     border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; margin: 28px 0 16px; }
h3 { font-size: 13px; font-weight: 600; margin-bottom: 6px; }

/* Finding cards */
.finding { background: white; border-radius: 8px; margin-bottom: 14px;
           box-shadow: 0 1px 3px rgba(0,0,0,.08); overflow: hidden; }
.finding-header { display: flex; align-items: center; gap: 10px;
                  padding: 12px 16px; border-left: 5px solid; }
.badge { font-size: 11px; font-weight: 700; padding: 2px 8px;
         border-radius: 4px; color: white; white-space: nowrap; }
.finding-title { font-weight: 600; font-size: 13px; flex: 1; }
.owasp-tag { font-size: 11px; color: #718096; background: #edf2f7;
             padding: 2px 7px; border-radius: 4px; white-space: nowrap; }
.finding-body { padding: 12px 16px; border-top: 1px solid #f0f0f0; }
.finding-body dl { display: grid; grid-template-columns: 100px 1fr; gap: 4px 12px; }
.finding-body dt { color: #718096; font-size: 12px; }
.finding-body dd { font-size: 12px; }
.evidence { font-family: monospace; font-size: 11px; background: #f7fafc;
            border: 1px solid #e2e8f0; border-radius: 4px;
            padding: 6px 10px; margin-top: 6px; word-break: break-all; }

/* Recommendations */
.rec { background: white; border-radius: 8px; margin-bottom: 14px;
       box-shadow: 0 1px 3px rgba(0,0,0,.08); padding: 16px; }
.rec-rule { font-size: 11px; font-weight: 700; color: #3182ce;
            background: #ebf8ff; padding: 2px 8px; border-radius: 4px;
            display: inline-block; margin-bottom: 10px; }
.rec-text { line-height: 1.6; white-space: pre-wrap; font-size: 12px; }
.rec-sources { margin-top: 10px; font-size: 11px; color: #718096;
               border-top: 1px solid #f0f0f0; padding-top: 8px; }

/* Coverage */
.owasp-list { display: flex; flex-wrap: wrap; gap: 8px; }
.owasp-chip { background: #1a202c; color: white; font-size: 11px; font-weight: 600;
              padding: 4px 12px; border-radius: 20px; }

/* Footer */
.footer { margin-top: 40px; text-align: center; font-size: 11px; color: #a0aec0; }
"""


def _e(text: str) -> str:
    """Escapa HTML para evitar XSS en datos del proyecto."""
    return html.escape(str(text))


def _finding_html(f: Union[Finding, DynamicFinding]) -> str:
    color = _SEVERITY_COLOR.get(f.severity, "#718096")
    bg = _SEVERITY_BG.get(f.severity, "#f7fafc")

    if isinstance(f, DynamicFinding):
        location_label = "Endpoint"
        location_value = f"{_e(f.method)} {_e(f.endpoint)}"
    else:
        location_label = "Archivo"
        location_value = f"{_e(f.file)}:{f.line}"

    return f"""
<div class="finding">
  <div class="finding-header" style="border-left-color:{color}; background:{bg};">
    <span class="badge" style="background:{color};">{_e(f.severity)}</span>
    <span class="finding-title">{_e(f.title)}</span>
    <span class="owasp-tag">{_e(f.owasp_id)}</span>
  </div>
  <div class="finding-body">
    <dl>
      <dt>Regla</dt><dd>{_e(f.rule_id)}</dd>
      <dt>{location_label}</dt><dd>{location_value}</dd>
      <dt>Descripción</dt><dd>{_e(f.description)}</dd>
    </dl>
    <div class="evidence">{_e(f.evidence)}</div>
  </div>
</div>"""


def _recommendation_html(rec) -> str:
    sources_html = ""
    if rec.sources:
        srcs = " &nbsp;|&nbsp; ".join(_e(s) for s in rec.sources)
        sources_html = f'<div class="rec-sources">Fuentes: {srcs}</div>'

    return f"""
<div class="rec">
  <span class="rec-rule">{_e(rec.rule_id)}</span>
  <div class="rec-text">{_e(rec.recommendation)}</div>
  {sources_html}
</div>"""


def render_html(report: AuditReport) -> str:
    """Genera el HTML completo del reporte."""
    m = report.metrics

    # Tarjetas de resumen
    cards = f"""
<div class="summary">
  <div class="card total"><div class="num">{m.total_findings}</div><div class="lbl">Total</div></div>
  <div class="card high"><div class="num">{m.high}</div><div class="lbl">High</div></div>
  <div class="card medium"><div class="num">{m.medium}</div><div class="lbl">Medium</div></div>
  <div class="card low"><div class="num">{m.low}</div><div class="lbl">Low</div></div>
  <div class="card info"><div class="num">{m.info}</div><div class="lbl">Info</div></div>
</div>"""

    # Hallazgos
    findings_html = "".join(_finding_html(f) for f in report.findings)
    if not findings_html:
        findings_html = "<p style='color:#718096'>No se encontraron hallazgos.</p>"

    # Recomendaciones
    recs_section = ""
    if report.recommendations:
        recs_html = "".join(_recommendation_html(r) for r in report.recommendations)
        recs_section = f"<h2>Recomendaciones LLM</h2>{recs_html}"

    # Cobertura OWASP
    chips = "".join(
        f'<span class="owasp-chip">{_e(oid)}</span>'
        for oid in m.owasp_coverage
    )
    coverage_section = f"""
<h2>Cobertura OWASP API Security Top 10</h2>
<div class="owasp-list">{chips if chips else '<span style="color:#718096">Ninguna</span>'}</div>"""

    # Métricas adicionales
    metrics_section = f"""
<h2>Métricas de la auditoría</h2>
<table style="border-collapse:collapse; width:100%; background:white;
              border-radius:8px; overflow:hidden;
              box-shadow:0 1px 3px rgba(0,0,0,.08);">
  <tr style="background:#f7fafc;">
    <td style="padding:10px 16px; font-weight:600; width:50%">Hallazgos estáticos (AST)</td>
    <td style="padding:10px 16px;">{m.static_count}</td>
  </tr>
  <tr>
    <td style="padding:10px 16px; font-weight:600;">Hallazgos dinámicos (HTTP)</td>
    <td style="padding:10px 16px;">{m.dynamic_count}</td>
  </tr>
  <tr style="background:#f7fafc;">
    <td style="padding:10px 16px; font-weight:600;">Recomendaciones LLM generadas</td>
    <td style="padding:10px 16px;">{m.recommendations_count}</td>
  </tr>
  <tr>
    <td style="padding:10px 16px; font-weight:600;">Categorías OWASP detectadas</td>
    <td style="padding:10px 16px;">{len(m.owasp_coverage)} / 10</td>
  </tr>
</table>"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reporte de Auditoría DRF</title>
  <style>{_CSS}</style>
</head>
<body>
<div class="page">
  <div class="header">
    <h1>Reporte de Auditoría de Seguridad</h1>
    <div class="meta">
      Proyecto: {_e(report.project_path)} &nbsp;&bull;&nbsp;
      Generado: {_e(report.generated_at)}
    </div>
  </div>

  {cards}

  <h2>Hallazgos ({m.total_findings})</h2>
  {findings_html}

  {recs_section}

  {coverage_section}

  {metrics_section}

  <div class="footer">
    Generado por Auditor DRF &mdash; OWASP API Security Top 10 (2023)
  </div>
</div>
</body>
</html>"""
