from abc import ABC, abstractmethod
from typing import List
import requests
from ..findings import DynamicFinding


class BaseProbe(ABC):
    """Clase base para todas las pruebas dinámicas."""

    def __init__(self, base_url: str, session: requests.Session):
        self.base_url = base_url.rstrip("/")
        self.session = session

    def url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    @abstractmethod
    def run(self) -> List[DynamicFinding]:
        """Ejecuta la prueba y retorna hallazgos encontrados."""
        ...
