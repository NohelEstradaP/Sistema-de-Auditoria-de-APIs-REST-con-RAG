import sys
import click
from pathlib import Path

from .static_analyzer import scan_project
from .dynamic_analyzer import run_dynamic_analysis
from .dynamic_analyzer.findings import DynamicFinding

_SEVERITY_COLOR = {
    "HIGH": "red",
    "MEDIUM": "yellow",
    "LOW": "cyan",
    "INFO": "white",
}


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
def scan(project_path: str, static: bool, dynamic_url: str):
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

    high_count = sum(1 for f in all_findings if f.severity == "HIGH")
    sys.exit(1 if high_count > 0 else 0)
