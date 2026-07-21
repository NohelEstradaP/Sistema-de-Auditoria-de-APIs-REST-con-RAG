"""
Exportador de reportes — Fase 7.

Convierte un AuditReport a HTML o PDF.
PDF generado con ReportLab (puro Python, sin dependencias del sistema).
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from .builder import AuditReport
from .html_template import render_html

# Colores de severidad para PDF
_SEV_COLOR = {
    "HIGH":   (0.898, 0.243, 0.243),
    "MEDIUM": (0.867, 0.420, 0.125),
    "LOW":    (0.196, 0.506, 0.808),
    "INFO":   (0.443, 0.502, 0.588),
}


def export_html(report: AuditReport, output_path: str) -> str:
    """
    Exporta el reporte como archivo HTML.

    Args:
        report: AuditReport construido por build_report().
        output_path: Ruta de destino (ej. "reporte.html").

    Returns:
        Ruta absoluta del archivo generado.
    """
    path = Path(output_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_html(report), encoding="utf-8")
    return str(path)


def export_pdf(report: AuditReport, output_path: str) -> str:
    """
    Exporta el reporte como archivo PDF usando ReportLab.

    Args:
        report: AuditReport construido por build_report().
        output_path: Ruta de destino (ej. "reporte.pdf").

    Returns:
        Ruta absoluta del archivo generado.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether,
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER

    path = Path(output_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    W = A4[0] - 36 * mm  # ancho útil

    s_title = ParagraphStyle("title", parent=styles["Title"],
                             fontSize=18, textColor=colors.HexColor("#1a202c"),
                             spaceAfter=4)
    s_meta  = ParagraphStyle("meta",  parent=styles["Normal"],
                             fontSize=9, textColor=colors.HexColor("#718096"),
                             spaceAfter=12)
    s_h2    = ParagraphStyle("h2",    parent=styles["Heading2"],
                             fontSize=13, textColor=colors.HexColor("#1a202c"),
                             spaceBefore=14, spaceAfter=6,
                             borderPad=2)
    s_body  = ParagraphStyle("body",  parent=styles["Normal"],
                             fontSize=9, leading=13, spaceAfter=4)
    s_mono  = ParagraphStyle("mono",  parent=styles["Code"],
                             fontSize=8, leading=11,
                             backColor=colors.HexColor("#f7fafc"),
                             borderColor=colors.HexColor("#e2e8f0"),
                             borderWidth=0.5, borderPad=4,
                             spaceAfter=4)
    s_rec   = ParagraphStyle("rec",   parent=styles["Normal"],
                             fontSize=9, leading=13, spaceAfter=4,
                             leftIndent=6)

    story = []

    # ── Encabezado ────────────────────────────
    story.append(Paragraph("Reporte de Auditoría de Seguridad DRF", s_title))
    story.append(Paragraph(
        f"Proyecto: {report.project_path} &nbsp;|&nbsp; Generado: {report.generated_at}",
        s_meta,
    ))
    story.append(HRFlowable(width=W, thickness=1, color=colors.HexColor("#e2e8f0"),
                            spaceAfter=12))

    # ── Tarjetas de resumen ───────────────────
    m = report.metrics
    summary_data = [
        ["Total", "HIGH", "MEDIUM", "LOW", "INFO"],
        [str(m.total_findings), str(m.high), str(m.medium), str(m.low), str(m.info)],
    ]
    summary_table = Table(summary_data, colWidths=[W / 5] * 5)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a202c")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 9),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME",   (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 1), (-1, 1), 20),
        ("TEXTCOLOR",  (1, 1), (1, 1), colors.HexColor("#e53e3e")),
        ("TEXTCOLOR",  (2, 1), (2, 1), colors.HexColor("#dd6b20")),
        ("TEXTCOLOR",  (3, 1), (3, 1), colors.HexColor("#3182ce")),
        ("TEXTCOLOR",  (4, 1), (4, 1), colors.HexColor("#718096")),
        ("ROWBACKGROUNDS", (0, 1), (-1, 1), [colors.white]),
        ("BOX",        (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("INNERGRID",  (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING",  (0, 1), (-1, 1), 8),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 14))

    # ── Hallazgos ─────────────────────────────
    story.append(Paragraph(f"Hallazgos ({m.total_findings})", s_h2))

    from ..dynamic_analyzer.findings import DynamicFinding

    for f in report.findings:
        r, g, b = _SEV_COLOR.get(f.severity, (0.4, 0.5, 0.6))
        sev_color = colors.Color(r, g, b)

        if isinstance(f, DynamicFinding):
            location = f"{f.method} {f.endpoint}"
            loc_label = "Endpoint"
        else:
            location = f"{f.file}:{f.line}"
            loc_label = "Archivo"

        header = Table(
            [[Paragraph(f"<b>{f.severity}</b>", ParagraphStyle(
                "bh", parent=s_body, fontSize=8, textColor=colors.white)),
              Paragraph(f"<b>{f.title}</b>", ParagraphStyle(
                "th", parent=s_body, textColor=colors.HexColor("#1a202c"))),
              Paragraph(f.owasp_id, ParagraphStyle(
                "oh", parent=s_body, fontSize=8,
                textColor=colors.HexColor("#718096")))]],
            colWidths=[14 * mm, W - 36 * mm, 18 * mm],
        )
        header.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), sev_color),
            ("BACKGROUND", (1, 0), (-1, 0), colors.HexColor("#f7fafc")),
            ("ALIGN", (0, 0), (0, 0), "CENTER"),
            ("ALIGN", (2, 0), (2, 0), "RIGHT"),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("TOPPADDING",  (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("LEFTPADDING", (1, 0), (1, 0), 8),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ]))

        detail = Table(
            [
                [Paragraph("<b>Regla</b>", s_body),     Paragraph(f.rule_id, s_body)],
                [Paragraph(f"<b>{loc_label}</b>", s_body), Paragraph(location, s_body)],
                [Paragraph("<b>Descripción</b>", s_body), Paragraph(f.description, s_body)],
                [Paragraph("<b>Evidencia</b>", s_body),
                 Paragraph(f.evidence[:200], s_mono)],
            ],
            colWidths=[22 * mm, W - 22 * mm],
        )
        detail.setStyle(TableStyle([
            ("VALIGN",     (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (0, -1), 8),
            ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            ("BOX",        (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("LINEBELOW",  (0, 0), (-1, -2), 0.3, colors.HexColor("#f0f0f0")),
        ]))

        story.append(KeepTogether([header, detail, Spacer(1, 6)]))

    # ── Recomendaciones LLM ───────────────────
    if report.recommendations:
        story.append(Paragraph("Recomendaciones LLM (RAG)", s_h2))
        for rec in report.recommendations:
            label = Paragraph(
                f'<font color="#3182ce"><b>{rec.rule_id}</b></font>', s_body)
            text  = Paragraph(rec.recommendation.replace("\n", "<br/>"), s_rec)
            sources_text = ""
            if rec.sources:
                sources_text = "Fuentes: " + " | ".join(rec.sources)
            src = Paragraph(f'<font color="#718096" size="8">{sources_text}</font>',
                            s_body) if sources_text else Spacer(1, 0)
            block = Table(
                [[label], [text], [src]],
                colWidths=[W],
            )
            block.setStyle(TableStyle([
                ("BOX",        (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING",  (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(KeepTogether([block, Spacer(1, 6)]))

    # ── Cobertura OWASP ───────────────────────
    story.append(Paragraph("Cobertura OWASP API Security Top 10", s_h2))
    if m.owasp_coverage:
        chips_data = [[Paragraph(
            f'<font color="white"><b>{oid}</b></font>', ParagraphStyle(
                "chip", parent=s_body, alignment=TA_CENTER))
            for oid in m.owasp_coverage]]
        chips_table = Table(chips_data,
                            colWidths=[22 * mm] * len(m.owasp_coverage))
        chips_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#1a202c")),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("ROUNDEDCORNERS", [4]),
        ]))
        story.append(chips_table)
    story.append(Spacer(1, 14))

    # ── Métricas ──────────────────────────────
    story.append(Paragraph("Métricas de la auditoría", s_h2))
    metrics_data = [
        ["Hallazgos estáticos (AST)",           str(m.static_count)],
        ["Hallazgos dinámicos (HTTP)",           str(m.dynamic_count)],
        ["Recomendaciones LLM generadas",        str(m.recommendations_count)],
        ["Categorías OWASP detectadas",          f"{len(m.owasp_coverage)} / 10"],
    ]
    metrics_table = Table(metrics_data, colWidths=[W * 0.7, W * 0.3])
    metrics_table.setStyle(TableStyle([
        ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [colors.HexColor("#f7fafc"), colors.white]),
        ("BOX",        (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("INNERGRID",  (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
    ]))
    story.append(metrics_table)

    # ── Footer ────────────────────────────────
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width=W, thickness=0.5,
                             color=colors.HexColor("#e2e8f0"), spaceAfter=6))
    story.append(Paragraph(
        "Generado por Auditor DRF — OWASP API Security Top 10 (2023)",
        ParagraphStyle("footer", parent=s_body, fontSize=8,
                       textColor=colors.HexColor("#a0aec0"),
                       alignment=TA_CENTER),
    ))

    doc.build(story)
    return str(path)


def export(report: AuditReport, output_path: str) -> str:
    """
    Exporta el reporte al formato inferido de la extensión del archivo.
    Soporta .html y .pdf.
    """
    ext = Path(output_path).suffix.lower()
    if ext == ".pdf":
        return export_pdf(report, output_path)
    if ext in (".html", ".htm"):
        return export_html(report, output_path)
    raise ValueError(f"Extensión no soportada: '{ext}'. Usa .html o .pdf")
