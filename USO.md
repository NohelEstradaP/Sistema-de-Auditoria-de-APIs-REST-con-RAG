# Guía de Uso — Auditor de Seguridad DRF

Herramienta CLI para auditoría automatizada de seguridad en proyectos Django REST Framework.
Detecta vulnerabilidades OWASP API Security Top 10 mediante análisis estático (AST) y dinámico (HTTP),
enriquecidas con recomendaciones generadas por un LLM local (Ollama) a través de un pipeline RAG.

> Funciona **100% localmente** — sin llamadas a APIs externas.

---

## Requisitos previos

| Componente | Versión mínima |
|---|---|
| Python | 3.11+ |
| Ollama | 0.20+ |
| RAM | 8 GB (para Mistral 7B + ChromaDB) |
| Espacio en disco | ~6 GB (modelo + vectores + docs) |

---

## Instalación

```bash
# Clonar o situarse en el directorio del proyecto
cd tesis_proyecto

# Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows

# Instalar dependencias
pip install -r requirements.txt
```

---

## Configuración inicial de Ollama

Ollama debe estar corriendo antes de usar las funciones RAG/LLM.

```bash
# Iniciar el servidor Ollama (si no está ya corriendo)
ollama serve

# Descargar el modelo (solo la primera vez, ~4 GB)
ollama pull mistral

# Verificar que el modelo está disponible
ollama list
```

---

## Preparar la API vulnerable (laboratorio de pruebas)

La carpeta `vulnerable_api/` contiene una API Django con vulnerabilidades OWASP intencionales
para validar el auditor.

```bash
cd vulnerable_api

# Aplicar migraciones
python manage.py migrate

# Poblar con datos de prueba (alice, bob, admin)
python seed.py

# Iniciar la API en el puerto 8000
python manage.py runserver 8000
```

Usuarios disponibles tras el seed:

| Usuario | Contraseña | Rol |
|---|---|---|
| alice | alice123 | Usuario normal |
| bob | bob123 | Usuario normal |
| admin | admin123 | Administrador |

---

## Indexar la knowledge base

Antes de usar las recomendaciones LLM, hay que vectorizar los documentos OWASP/DRF en ChromaDB.
Solo se necesita hacer una vez (o cuando se actualicen los documentos).

```bash
# Desde la raíz del proyecto, con venv activo
python -m auditor index-kb
```

Opciones disponibles:

```bash
python -m auditor index-kb --help

# Usar un directorio de KB personalizado
python -m auditor index-kb --kb-dir ./mi_knowledge_base

# Forzar re-indexación desde cero
python -m auditor index-kb --reset

# Persistir ChromaDB en una ruta específica
python -m auditor index-kb --chroma-dir /ruta/chroma_db
```

Documentos indexados por defecto (en `knowledge_base/`):

- `owasp_api_top10_2023.md` — OWASP API Security Top 10 (2023)
- `drf_security_guide.md` — Guía de seguridad de Django REST Framework
- `django_cves.md` — CVEs relevantes de Django y checklist de hardening

---

## Auditar un proyecto

### Solo análisis estático (por defecto)

Inspecciona el código fuente sin necesitar la API corriendo.

```bash
python -m auditor scan /ruta/al/proyecto/django
```

Ejemplo contra la API vulnerable incluida:

```bash
python -m auditor scan ./vulnerable_api
```

Vulnerabilidades que detecta el analizador estático:

| Patrón | OWASP | Severidad |
|---|---|---|
| Vista sin `permission_classes` | API2 | HIGH |
| Serializer con campos sensibles sin `read_only` (`password`, `is_admin`) | API3 | HIGH |
| Parámetro numérico en URL sin verificación de ownership | API1 | HIGH |
| `DEBUG = True` en settings | API8 | MEDIUM |
| Sin `DEFAULT_THROTTLE_CLASSES` en settings | API4 | MEDIUM |
| Sin configuración `SIMPLE_JWT` | API2 | LOW |

### Análisis estático + dinámico

Requiere la API corriendo (ver sección "Preparar la API vulnerable").

```bash
python -m auditor scan ./vulnerable_api --dynamic http://localhost:8000
```

Pruebas que ejecuta el analizador dinámico:

| Prueba | OWASP | Severidad |
|---|---|---|
| GET sin token → espera 401 | API2 | HIGH |
| Acceder a objeto de otro usuario (BOLA) | API1 | HIGH |
| POST con `is_admin=true` → mass assignment | API3 | HIGH |
| 20 requests sin recibir 429 | API4 | MEDIUM |
| Endpoint admin accesible sin rol | API5 | HIGH |

### Solo análisis dinámico (sin estático)

```bash
python -m auditor scan ./vulnerable_api --no-static --dynamic http://localhost:8000
```

### Con recomendaciones LLM (RAG)

Enriquece cada hallazgo HIGH/MEDIUM con una recomendación generada por Mistral,
fundamentada en los fragmentos de documentación más relevantes de la KB.

> Requiere: Ollama corriendo + KB indexada.

```bash
python -m auditor scan ./vulnerable_api --rag
```

Combinando estático + dinámico + RAG:

```bash
python -m auditor scan ./vulnerable_api \
    --dynamic http://localhost:8000 \
    --rag \
    --model mistral
```

Opciones de RAG:

```bash
--rag                    # Activar recomendaciones LLM
--model TEXT             # Modelo Ollama (default: mistral)
--chroma-dir TEXT        # Ruta alternativa a ChromaDB
```

---

## Opciones completas del comando scan

```
python -m auditor scan [OPTIONS] PROJECT_PATH

Opciones:
  --static / --no-static    Análisis estático AST       [default: activo]
  --dynamic URL             URL base para análisis dinámico
  --rag                     Activar recomendaciones LLM con RAG
  --model TEXT              Modelo Ollama                [default: mistral]
  --chroma-dir TEXT         Directorio ChromaDB
  --help                    Mostrar ayuda
```

**Código de salida:**
- `0` — No se encontraron hallazgos HIGH
- `1` — Se encontró al menos un hallazgo HIGH (útil para integrar en CI/CD)

---

## Ejecutar los tests

```bash
# Todos los tests
pytest

# Solo tests estáticos (rápidos, sin dependencias externas)
pytest tests/test_static/ -v

# Solo tests dinámicos (HTTP mockeado, sin API corriendo)
pytest tests/test_dynamic/ -v

# Solo tests RAG (ChromaDB + sentence-transformers, ~2 min)
pytest tests/test_rag/ -v

# Un test específico
pytest tests/test_static/test_missing_permission_classes.py::test_missing_permission_detected
```

---

## Estructura del proyecto

```
tesis_proyecto/
├── auditor/
│   ├── static_analyzer/        # Análisis estático AST
│   │   ├── rules/              # Una regla por patrón de vulnerabilidad
│   │   ├── scanner.py          # Recorre archivos .py del proyecto
│   │   └── findings.py         # Dataclass Finding
│   ├── dynamic_analyzer/       # Análisis dinámico HTTP
│   │   ├── probes/             # Una probe por tipo de prueba
│   │   ├── runner.py           # Orquestador de probes
│   │   └── findings.py         # Dataclass DynamicFinding
│   ├── rag/
│   │   ├── indexer.py          # Carga docs → chunks → ChromaDB
│   │   ├── retriever.py        # Búsqueda por similitud coseno
│   │   └── generator.py        # Prompt + Ollama → LLMRecommendation
│   ├── cli.py                  # Comandos: scan, index-kb
│   └── config.py               # Rutas por defecto
├── knowledge_base/
│   ├── owasp_api_top10_2023.md
│   ├── drf_security_guide.md
│   └── django_cves.md
├── vulnerable_api/             # API Django con vulnerabilidades intencionales
│   ├── core/
│   │   ├── models.py
│   │   ├── serializers.py      # Vulnerabilidades API3
│   │   ├── views.py            # Vulnerabilidades API1, API2, API5
│   │   └── urls.py
│   └── seed.py                 # Datos de prueba
├── tests/
│   ├── test_static/            # 30 tests
│   ├── test_dynamic/           # 22 tests
│   └── test_rag/               # 30 tests
├── requirements.txt
├── DESARROLLO.md               # Estado de fases y plan de implementación
└── USO.md                      # Este archivo
```

---

## Flujo RAG (cómo funciona internamente)

```
Hallazgo
   │
   ▼
retrieve_for_finding(rule_id, description)
   │  Genera query semántica según OWASP ID
   │
   ▼
ChromaDB  ←──── sentence-transformers (all-MiniLM-L6-v2)
   │  Top-4 chunks más relevantes (similitud coseno)
   │
   ▼
build_prompt(hallazgo + chunks)
   │  Prompt estructurado con contexto OWASP/DRF
   │
   ▼
Ollama (mistral)
   │  temperature=0.2, max_tokens=512
   │
   ▼
LLMRecommendation
   ├── recommendation  (texto generado)
   ├── sources         (documentos citados)
   └── chunks_used     (fragmentos recuperados con score)
```

---

## Exportar reporte

El flag `--output` acepta `.html` o `.pdf` y puede combinarse con cualquier modo de análisis.

```bash
# Solo HTML
python -m auditor scan ./vulnerable_api --output reporte.html

# PDF completo con análisis estático + dinámico + RAG
python -m auditor scan ./vulnerable_api \
    --dynamic http://localhost:8000 \
    --rag \
    --output reporte.pdf
```

El reporte incluye:
- Resumen ejecutivo con conteo por severidad
- Hallazgos detallados (estáticos y dinámicos) ordenados por severidad
- Recomendaciones LLM con citas a documentación OWASP/DRF (si se usó `--rag`)
- Cobertura OWASP API Top 10 detectada
- Métricas de la auditoría

---

## Pendiente

- [ ] Evaluación comparativa RAG vs. sin RAG (para la defensa)
