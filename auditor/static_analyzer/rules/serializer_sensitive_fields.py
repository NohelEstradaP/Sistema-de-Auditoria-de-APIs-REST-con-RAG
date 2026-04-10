import ast
from typing import List, Optional, Set
from .base import BaseRule
from ..findings import Finding

SENSITIVE_FIELDS: Set[str] = {"password", "is_admin", "is_staff", "is_superuser", "secret"}

_SERIALIZER_BASES: Set[str] = {
    "ModelSerializer",
    "Serializer",
    "HyperlinkedModelSerializer",
}


def _is_serializer_class(bases: list) -> bool:
    for base in bases:
        name = None
        if isinstance(base, ast.Name):
            name = base.id
        elif isinstance(base, ast.Attribute):
            name = base.attr
        if name in _SERIALIZER_BASES:
            return True
    return False


def _get_meta_fields(class_node: ast.ClassDef) -> Optional[ast.expr]:
    """Retorna el nodo de la asignación `fields` dentro de Meta, o None."""
    for node in class_node.body:
        if isinstance(node, ast.ClassDef) and node.name == "Meta":
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "fields":
                            return item.value
    return None


def _explicit_read_only_fields(class_node: ast.ClassDef) -> Set[str]:
    """
    Retorna los nombres de campos declarados explícitamente con read_only=True,
    ya sea como atributos de clase o en extra_kwargs (dentro o fuera de Meta).
    """
    read_only: Set[str] = set()

    # Busca en el cuerpo del serializer y dentro de Meta
    nodes_to_check = list(class_node.body)
    for node in class_node.body:
        if isinstance(node, ast.ClassDef) and node.name == "Meta":
            nodes_to_check.extend(node.body)

    for node in nodes_to_check:
        # Caso 1: field = serializers.CharField(read_only=True)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                if isinstance(node.value, ast.Call):
                    for kw in node.value.keywords:
                        if kw.arg == "read_only" and isinstance(kw.value, ast.Constant):
                            if kw.value.value is True:
                                read_only.add(target.id)

        # Caso 2: extra_kwargs = {'password': {'read_only': True}}
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if not (isinstance(target, ast.Name) and target.id == "extra_kwargs"):
                    continue
                if not isinstance(node.value, ast.Dict):
                    continue
                for key, val in zip(node.value.keys, node.value.values):
                    if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
                        continue
                    if not isinstance(val, ast.Dict):
                        continue
                    for ek, ev in zip(val.keys, val.values):
                        if (
                            isinstance(ek, ast.Constant) and ek.value == "read_only"
                            and isinstance(ev, ast.Constant) and ev.value is True
                        ):
                            read_only.add(key.value)

    return read_only


class SerializerSensitiveFieldsRule(BaseRule):
    """
    API3 — Detecta serializers que exponen campos sensibles sin read_only.
    Un campo como `password` o `is_admin` listado en Meta.fields y escribible
    permite que el cliente lo modifique directamente (mass assignment).
    """

    def check(self, tree: ast.AST, filepath: str, source: str) -> List[Finding]:
        findings = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not _is_serializer_class(node.bases):
                continue

            fields_node = _get_meta_fields(node)
            if fields_node is None:
                continue

            # fields = '__all__'  → advertencia genérica
            if isinstance(fields_node, ast.Constant) and fields_node.value == "__all__":
                findings.append(Finding(
                    rule_id="API3-FIELDS-ALL",
                    owasp_id="API3",
                    title=f"Serializer '{node.name}' usa fields='__all__'",
                    severity="MEDIUM",
                    file=filepath,
                    line=node.lineno,
                    description=(
                        f"'{node.name}' expone todos los campos del modelo con fields='__all__'. "
                        "Esto puede incluir campos sensibles no intencionados. "
                        "Enumera explícitamente los campos permitidos."
                    ),
                    evidence=self._get_line(source, node.lineno),
                ))
                continue

            # fields = ['field1', 'field2', ...]
            if not isinstance(fields_node, (ast.List, ast.Tuple)):
                continue

            declared_fields = {
                elt.value
                for elt in fields_node.elts
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            }

            read_only_fields = _explicit_read_only_fields(node)
            exposed_sensitive = declared_fields & SENSITIVE_FIELDS - read_only_fields

            for field_name in sorted(exposed_sensitive):
                findings.append(Finding(
                    rule_id="API3-SENSITIVE-FIELD",
                    owasp_id="API3",
                    title=f"Campo sensible '{field_name}' expuesto sin read_only en '{node.name}'",
                    severity="HIGH",
                    file=filepath,
                    line=node.lineno,
                    description=(
                        f"El serializer '{node.name}' incluye '{field_name}' en Meta.fields "
                        "sin marcarlo como read_only. Un cliente puede modificar este campo "
                        "directamente en una petición POST/PUT/PATCH (mass assignment)."
                    ),
                    evidence=self._get_line(source, node.lineno),
                ))

        return findings
