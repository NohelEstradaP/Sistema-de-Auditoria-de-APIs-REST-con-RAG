import sys
import click
from pathlib import Path

from .static_analyzer import scan_project
from .dynamic_analyzer import run_dynamic_analysis
from .dynamic_analyzer.findings import DynamicFinding
from .rag.indexer import index_knowledge_base
from .rag.generator import enrich_findings, DEFAULT_MODEL
from .report import build_report, export
from .config import DEFAULT_KB_DIR, DEFAULT_CHROMA_DIR

_SEVERITY_COLOR = {
    "HIGH": "red",
    "MEDIUM": "yellow",
    "LOW": "cyan",
    "INFO": "white",
}


def _print_recommendations(recommendations):
    if not recommendations:
        return
    click.echo()
    click.secho("═" * 60, bold=True)
    click.secho("  RECOMENDACIONES LLM (con RAG)", bold=True)
    click.secho("═" * 60, bold=True)
    for rec in recommendations:
        click.secho(f"\n▶ {rec.rule_id}", fg="cyan", bold=True)
        click.echo(rec.recommendation)
        if rec.sources:
            click.secho("  Fuentes: " + " | ".join(rec.sources), fg="white")


def _print_findings(findings):
    if not findings:
        click.secho("No se encontraron hallazgos.", fg="green")
        return

    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for f in findings:
        counts[f.severity] += 1

    click.echo()
    for f in findings:
        color = _SEVERITY_COLOR.get(f.severity, "white")
        click.secho(f"[{f.severity}] {f.rule_id}", fg=color, bold=True)
        click.echo(f"  Título   : {f.title}")
        click.echo(f"  OWASP    : {f.owasp_id}")
        if isinstance(f, DynamicFinding):
            click.echo(f"  Endpoint : {f.method} {f.endpoint}")
        else:
            click.echo(f"  Archivo  : {f.file}:{f.line}")
        click.echo(f"  Evidencia: {f.evidence}")
        click.echo(f"  Detalle  : {f.description}")
        click.echo()

    click.echo("─" * 60)
    click.secho(
        f"Total: {len(findings)} hallazgo(s)  |  "
        f"HIGH={counts['HIGH']}  MEDIUM={counts['MEDIUM']}  "
        f"LOW={counts['LOW']}  INFO={counts['INFO']}",
        bold=True,
    )


@click.group()
def cli():
    """Auditor de seguridad para proyectos Django REST Framework."""


@cli.command("scan")
@click.argument("project_path", type=click.Path(exists=True, file_okay=False))
@click.option("--static/--no-static", default=True, show_default=True,
              help="Ejecutar análisis estático (AST).")
@click.option("--dynamic", "dynamic_url", default=None, metavar="URL",
              help="URL base de la API para análisis dinámico (ej. http://localhost:8000).")
@click.option("--rag", is_flag=True, default=False,
              help="Enriquecer hallazgos con recomendaciones LLM vía RAG (requiere Ollama).")
@click.option("--model", default=DEFAULT_MODEL, show_default=True,
              help="Modelo Ollama a usar para las recomendaciones RAG.")
@click.option("--chroma-dir", default=DEFAULT_CHROMA_DIR, show_default=True,
              help="Directorio ChromaDB con la knowledge base indexada.")
@click.option("--output", "output_path", default=None, metavar="FILE",
              help="Exportar reporte a FILE (.html o .pdf).")
def scan(project_path: str, static: bool, dynamic_url: str,
         rag: bool, model: str, chroma_dir: str, output_path: str):
    """Audita PROJECT_PATH en busca de vulnerabilidades OWASP API Top 10."""
    path = Path(project_path).resolve()
    click.echo(f"Auditando: {path}")

    all_findings = []

    if static:
        click.echo("→ Análisis estático...")
        findings = scan_project(str(path))
        all_findings.extend(findings)
        click.echo(f"  {len(findings)} hallazgo(s) encontrado(s).")

    if dynamic_url:
        click.echo(f"→ Análisis dinámico contra {dynamic_url} ...")
        findings = run_dynamic_analysis(dynamic_url)
        all_findings.extend(findings)
        click.echo(f"  {len(findings)} hallazgo(s) encontrado(s).")

    _print_findings(all_findings)

    recs = []
    if rag and all_findings:
        click.echo(f"\n→ Generando recomendaciones con RAG ({model})...")
        try:
            recs = enrich_findings(all_findings, chroma_dir=chroma_dir, model=model)
            click.echo(f"  {len(recs)} recomendación(es) generada(s).")
            _print_recommendations(recs)
        except Exception as exc:
            click.secho(f"  Advertencia RAG: {exc}", fg="yellow")

    if output_path:
        click.echo(f"\n→ Exportando reporte a {output_path} ...")
        try:
            report = build_report(str(path), all_findings, recs)
            saved = export(report, output_path)
            click.secho(f"  Reporte guardado: {saved}", fg="green")
        except Exception as exc:
            click.secho(f"  Error al exportar: {exc}", fg="red", err=True)

    high_count = sum(1 for f in all_findings if f.severity == "HIGH")
    sys.exit(1 if high_count > 0 else 0)


@cli.command("index-kb")
@click.option("--kb-dir", default=DEFAULT_KB_DIR, show_default=True,
              help="Directorio con los documentos de la knowledge base.")
@click.option("--chroma-dir", default=DEFAULT_CHROMA_DIR, show_default=True,
              help="Directorio donde ChromaDB persiste los vectores.")
@click.option("--reset", is_flag=True, default=False,
              help="Eliminar la colección existente antes de indexar.")
def index_kb(kb_dir: str, chroma_dir: str, reset: bool):
    """Vectoriza la knowledge base OWASP/DRF en ChromaDB."""
    click.echo(f"Indexando documentos de: {kb_dir}")
    click.echo(f"ChromaDB en: {chroma_dir}")
    if reset:
        click.secho("  Modo reset: se eliminará la colección existente.", fg="yellow")

    try:
        count = index_knowledge_base(kb_dir, chroma_dir, reset=reset)
        click.secho(f"  {count} chunks indexados correctamente.", fg="green")
    except Exception as exc:
        click.secho(f"Error al indexar: {exc}", fg="red", err=True)
        sys.exit(1)
