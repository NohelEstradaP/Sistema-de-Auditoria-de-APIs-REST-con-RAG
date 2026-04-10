import ast
from typing import List, Set
from .base import BaseRule
from ..findings import Finding

# Clases base de DRF que definen vistas (sin el prefijo de módulo)
_DRF_VIEW_BASES: Set[str] = {
    "APIView",
    "GenericAPIView",
    "ListAPIView",
    "CreateAPIView",
    "RetrieveAPIView",
    "UpdateAPIView",
    "DestroyAPIView",
    "ListCreateAPIView",
    "RetrieveUpdateAPIView",
    "RetrieveDestroyAPIView",
    "RetrieveUpdateDestroyAPIView",
    "ViewSet",
    "ModelViewSet",
    "ReadOnlyModelViewSet",
    "GenericViewSet",
}


def _is_drf_view(bases: list) -> bool:
    """Retorna True si alguna de las bases es una clase de vista DRF."""
    for base in bases:
        name = None
        if isinstance(base, ast.Name):
            name = base.id
        elif isinstance(base, ast.Attribute):
            name = base.attr
        if name in _DRF_VIEW_BASES:
            return True
    return False


def _has_permission_classes(class_node: ast.ClassDef) -> bool:
    """Retorna True si la clase define permission_classes como atributo."""
    for node in class_node.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "permission_classes":
                    return True
        # permission_classes: ClassVar[...] = [...]  (anotada)
        if isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "permission_classes":
                return True
    return False


class MissingPermissionClassesRule(BaseRule):
    """
    API2 — Detecta vistas DRF sin permission_classes definido.
    Sin permisos explícitos, la vista hereda el default global (AllowAny si no
    se configuró DEFAULT_PERMISSION_CLASSES), permitiendo acceso anónimo.
    """

    def check(self, tree: ast.AST, filepath: str, source: str) -> List[Finding]:
        findings = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not _is_drf_view(node.bases):
                continue
            if not _has_permission_classes(node):
                findings.append(Finding(
                    rule_id="API2-NO-PERMISSION",
                    owasp_id="API2",
                    title=f"Vista '{node.name}' sin permission_classes",
                    severity="HIGH",
                    file=filepath,
                    line=node.lineno,
                    description=(
                        f"La vista '{node.name}' no define permission_classes. "
                        "Si DEFAULT_PERMISSION_CLASSES no está configurado en settings, "
                        "cualquier usuario anónimo puede acceder al endpoint."
                    ),
                    evidence=self._get_line(source, node.lineno),
                ))

        return findings
